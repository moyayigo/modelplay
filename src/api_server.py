import os
import json
import re
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.llm import LLMClient
from src.model_config import load_config, get_active_provider, save_config
from src.prompts import PromptManager, parse_tool_call
from src.token_tracker import check_limit, add_usage, get_today_usage, get_daily_limit, reset_usage

app = FastAPI(title="ModelPlay AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = None
prompt_manager = None

game_sessions: Dict[str, Dict[str, Any]] = {}


class GameStartRequest(BaseModel):
    game_type: str = "generic"
    game_prompt: Optional[str] = None


class GameMoveRequest(BaseModel):
    session_id: str
    player: str
    action: Optional[Any] = None
    board: Optional[Dict[str, Any]] = None
    status: str = "playing"


class GameResponse(BaseModel):
    session_id: str
    player: str
    action: Optional[Any] = None
    board: Optional[Dict[str, Any]] = None
    status: str
    message: Optional[str] = None


def init_components():
    global llm, prompt_manager
    provider = get_active_provider()
    if provider:
        llm = LLMClient.from_config(provider)
    else:
        llm = LLMClient()
    prompt_manager = PromptManager(active_modules=["game"])


@app.on_event("startup")
async def startup_event():
    init_components()
    print("API Server started.")


def _extract_json_response(text: str) -> Optional[Dict[str, Any]]:
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    brace_positions = []
    in_string = False
    escape = False
    for i, char in enumerate(text):
        if escape:
            escape = False
        elif char == '\\':
            escape = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_positions.append(i)

    for pos in reversed(brace_positions):
        segment = text[pos:]
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(segment)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    return None


def _format_strategy_dict(parsed: Dict[str, Any]) -> str:
    """将非标准策略分析字典转换为可读的 Markdown 文本。

    模型有时会忽略 prompt 要求的 {"strategic_analysis": "..."} 格式，
    返回 {"key_turning_points": [...], "strategic_pros_and_cons": {...}} 等结构。
    此函数将这些非标准结构转换为易读的 Markdown 文本，避免前端直接显示原始 JSON。
    """
    # 已知字段的中英文标题映射
    section_titles = {
        "key_turning_points": "Key Turning Points",
        "strategic_pros_and_cons": "Strategic Pros & Cons",
        "interesting_moves_or_mistakes": "Interesting Moves / Mistakes",
        "pros": "Pros",
        "cons": "Cons",
    }

    def _format_value(value: Any, indent: int = 0) -> str:
        pad = "  " * indent
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                if k in section_titles:
                    label = section_titles[k]
                else:
                    label = str(k).replace("_", " ").title()
                if isinstance(v, (dict, list)) and v:
                    lines.append(f"{pad}- **{label}**:")
                    lines.append(_format_value(v, indent + 1))
                else:
                    lines.append(f"{pad}- **{label}**: {v}")
            return "\n".join(lines)
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)) and item:
                    lines.append(f"{pad}-")
                    lines.append(_format_value(item, indent + 1))
                else:
                    lines.append(f"{pad}- {item}")
            return "\n".join(lines)
        return f"{pad}{value}"

    return _format_value(parsed)


@app.post("/api/game/start", response_model=GameResponse)
async def game_start(request: GameStartRequest):
    import uuid
    session_id = str(uuid.uuid4())[:8]

    game_sessions[session_id] = {
        "game_type": request.game_type,
        "game_prompt": request.game_prompt,
        "state": None,
        "turn": "user",
        "history": [],
        "status": "playing",
    }

    init_msg = {
        "player": "system",
        "action": None,
        "board": {"state": None, "turn": "user"},
        "status": "started",
    }

    game_sessions[session_id]["history"].append({"role": "system", "content": json.dumps(init_msg)})

    if request.game_prompt:
        game_sessions[session_id]["history"].append({
            "role": "system",
            "content": f"[Game Rules]\n{request.game_prompt}"
        })
        print(f"[DEBUG] Game started, game prompt saved to session")
        print(f"[DEBUG] game_prompt:\n{request.game_prompt}")

    return GameResponse(
        session_id=session_id,
        player="system",
        action=None,
        board={"state": None, "turn": "user"},
        status="started",
        message=f"Game started, session ID: {session_id}",
    )


@app.post("/api/game/move", response_model=GameResponse)
async def game_move(request: GameMoveRequest):
    if request.session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session does not exist, please start the game first")

    session = game_sessions[request.session_id]

    if request.player == "user":
        session["state"] = request.action
        session["turn"] = "model"
        session["history"].append({
            "role": "user",
            "content": json.dumps({
                "player": "user",
                "action": request.action,
                "board": request.board or {"state": request.action, "turn": "model"},
                "status": request.status,
            })
        })

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in session["history"]])

        system_prompt = prompt_manager.get_system_prompt()
        game_prompt = session.get("game_prompt", "")

        user_prompt = f"""Current game history:
{history_text}

The user just performed action: {json.dumps(request.action, ensure_ascii=False)}

Please make your response and return the action in JSON format."""

        print(f"\n[DEBUG] ===== Content sent to LLM =====")
        '''print(f"[DEBUG] System prompt (system_prompt):")
        print(f"---")
        print(system_prompt)
        print(f"---")
        print(f"[DEBUG] User prompt (user_prompt):")
        print(f"---")
        print(user_prompt)
        print(f"---")'''
        print(f"[DEBUG] User original action: {request.action}")
        print(f"[DEBUG] History count: {len(session['history'])}")
        print(f"=====================================\n")

        # 检查每日 token 限额
        limit_status = check_limit()
        if not limit_status["allowed"]:
            return GameResponse(
                session_id=request.session_id,
                player="system",
                action=None,
                board={"state": None, "turn": "user"},
                status="error",
                message=f"Today's token usage has reached the limit (used {limit_status['used']} / {limit_status['limit']}),"
                        f"please try again tomorrow or contact admin to adjust the limit.",
            )

        response = llm.call(prompt=user_prompt, system_prompt=system_prompt)

        # 累加本次调用的 token 使用量
        if getattr(llm, "last_usage", None):
            add_usage(
                llm.last_usage.get("prompt_tokens", 0),
                llm.last_usage.get("completion_tokens", 0),
            )

        print(f"[DEBUG] LLM raw response: {response}")

        parsed = _extract_json_response(response)
        #print(f"[DEBUG] JSON解析结果: {parsed}")

        model_action = None
        if parsed:
            if "move" in parsed:
                move_val = parsed["move"]
                if isinstance(move_val, dict):
                    model_action = move_val
                elif "move_data" in parsed and isinstance(parsed["move_data"], dict):
                    # 工具调用格式：move 是工具名（字符串），move_data 是参数
                    # 返回 move_data（包含实际的 code 等字段）
                    model_action = parsed["move_data"]
                else:
                    # 保留整个 parsed dict（如 {"move":"石头"}），而不是只取字符串值
                    # 这样前端能通过字段名提取值，不会丢失结构
                    model_action = parsed
            elif "action" in parsed:
                action_val = parsed["action"]
                if isinstance(action_val, dict):
                    model_action = action_val
                else:
                    model_action = parsed
            elif "result" in parsed:
                model_action = parsed["result"]
            else:
                model_action = parsed

        #print(f"[DEBUG] 模型动作: {model_action}")

        session["state"] = model_action
        session["turn"] = "user"
        session["history"].append({
            "role": "assistant",
            "content": json.dumps({
                "player": "assistant",
                "action": model_action,
                "board": {"state": model_action, "turn": "user"},
                "status": "playing",
            })
        })

        return GameResponse(
            session_id=request.session_id,
            player="assistant",
            action=model_action,
            board={"state": model_action, "turn": "user"},
            status="playing",
            message=f"Model response: {model_action}",
        )

    else:
        return GameResponse(
            session_id=request.session_id,
            player="system",
            status="error",
            message="Only users can initiate requests",
        )


@app.get("/api/game/status/{session_id}")
async def game_status(session_id: str):
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session does not exist")
    session = game_sessions[session_id]
    return {
        "session_id": session_id,
        "state": session["state"],
        "turn": session["turn"],
        "status": session["status"],
    }


@app.post("/api/game/end/{session_id}")
async def game_end(session_id: str):
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session does not exist")
    session = game_sessions[session_id]
    session["status"] = "ended"
    return {
        "session_id": session_id,
        "status": "ended",
        "result": session["state"],
    }


@app.post("/api/game/summary/{session_id}")
async def game_summary(session_id: str):
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session does not exist")
    session = game_sessions[session_id]

    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in session["history"]])

    summary_prompt = f"""Please analyze the following game process and provide a strategic analysis.

Game type: {session.get('game_type', 'unknown')}
Game history:
{history_text}

Return ONLY this exact JSON structure (no markdown, no extra text, no nested objects):
{{"strategic_analysis": "<your full analysis as a single string>"}}

CRITICAL FORMAT RULES:
1. The response MUST contain ONLY the field "strategic_analysis".
2. The value of "strategic_analysis" MUST be a single string (not a dict/list).
3. Put ALL your analysis inside this one string, using \\n for line breaks.
4. Do NOT use separate fields like "key_turning_points", "strategic_pros_and_cons", or "interesting_moves_or_mistakes".
5. Inside the string, organize your analysis with sections covering: key turning points, strategic pros/cons of both sides, and interesting moves/mistakes.

Example (correct):
{{"strategic_analysis": "Key Turning Points:\\n- User's opening move...\\n\\nStrategic Pros & Cons:\\n- User: ...\\n- AI: ...\\n\\nInteresting Moves:\\n- ..."}}

Example (WRONG - do not do this):
{{"key_turning_points": [...], "strategic_pros_and_cons": {{...}}}}"""

    system_prompt = "You are a game analyst, skilled at analyzing game strategies in concise English. Output only JSON with a single 'strategic_analysis' string field, no other text or structure."

    try:
        # 检查每日 token 限额
        limit_status = check_limit()
        if not limit_status["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Today's token usage has reached the limit (used {limit_status['used']} / {limit_status['limit']}),"
                       f"please try again tomorrow or contact admin to adjust the limit.",
            )

        response = llm.call(prompt=summary_prompt, system_prompt=system_prompt)

        # 累加本次调用的 token 使用量
        if getattr(llm, "last_usage", None):
            add_usage(
                llm.last_usage.get("prompt_tokens", 0),
                llm.last_usage.get("completion_tokens", 0),
            )

        parsed = _extract_json_response(response)
        print(f"[DEBUG] Game strategy analysis: {parsed}")
        strategic_analysis = ""
        if parsed and "strategic_analysis" in parsed:
            strategic_analysis = parsed["strategic_analysis"]
            # 防御性处理：模型偶尔会将 strategic_analysis 写成嵌套 dict 而非字符串
            if not isinstance(strategic_analysis, str):
                strategic_analysis = _format_strategy_dict(strategic_analysis)
        elif parsed and isinstance(parsed, dict):
            # 模型未遵循 {"strategic_analysis": "..."} 格式，返回了其他结构
            # 将其转换为可读的 Markdown 文本，避免前端直接显示原始 JSON
            strategic_analysis = _format_strategy_dict(parsed)
        else:
            strategic_analysis = response
        return {
            "session_id": session_id,
            "strategic_analysis": strategic_analysis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@app.get("/api/models/providers")
async def list_providers():
    config = load_config()
    return {
        "active_provider": config.get("active_provider", ""),
        "providers": config.get("providers", {}),
    }


@app.post("/api/models/switch/{provider_name}")
async def switch_provider(provider_name: str):
    config = load_config()
    providers = config.get("providers", {})
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' does not exist")
    config["active_provider"] = provider_name
    save_config(config)
    init_components()
    provider = providers[provider_name]
    mode = "Remote (API Key)" if provider.get("api_key", "").strip() else "Local"
    return {
        "active_provider": provider_name,
        "mode": mode,
        "model": provider.get("model", ""),
        "api_url": provider.get("api_url", ""),
    }


@app.post("/api/models/add")
async def add_provider(provider_name: str, name: str, model: str, api_url: str, api_key: str = "", max_tokens: int = 4096, timeout: int = 120):
    config = load_config()
    config["providers"][provider_name] = {
        "name": name,
        "model": model,
        "api_url": api_url,
        "api_key": api_key,
        "max_tokens": max_tokens,
        "timeout": timeout,
    }
    if not config.get("active_provider"):
        config["active_provider"] = provider_name
    save_config(config)
    return {"status": "ok", "provider": provider_name}


@app.delete("/api/models/delete/{provider_name}")
async def delete_provider(provider_name: str):
    config = load_config()
    providers = config.get("providers", {})
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' does not exist")
    if len(providers) <= 1:
        raise HTTPException(status_code=400, detail="At least one Provider must be retained")
    del providers[provider_name]
    if config.get("active_provider") == provider_name:
        config["active_provider"] = list(providers.keys())[0]
        init_components()
    save_config(config)
    return {"status": "ok"}


@app.post("/api/models/test/{provider_name}")
async def test_provider(provider_name: str):
    config = load_config()
    providers = config.get("providers", {})
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' does not exist")
    provider = providers[provider_name]
    test_client = LLMClient.from_config(provider)
    mode = "Remote" if provider.get("api_key", "").strip() else "Local"
    try:
        result = test_client.call(prompt="Hello, please reply with 'OK'", system_prompt="Reply with the simplest response")
        return {
            "status": "ok",
            "mode": mode,
            "response": result[:100] if result else "(empty)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@app.get("/api/usage")
async def get_usage():
    """Get today's token usage and limit status."""
    usage = get_today_usage()
    limit = get_daily_limit()
    used = usage.get("total_tokens", 0)
    remaining = -1 if limit <= 0 else max(0, limit - used)
    return {
        "date": usage.get("date"),
        "used": used,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "call_count": usage.get("call_count", 0),
        "limit": limit,
        "remaining": remaining,
        "allowed": remaining == -1 or remaining > 0,
        "reset_at": "Automatic reset at 00:00 every day",
    }


@app.post("/api/usage/reset")
async def api_reset_usage():
    """Manually reset today's token usage (admin operation)."""
    reset_usage()
    return {"status": "ok", "message": "Today's token usage has been reset"}


@app.get("/")
async def root():
    return {"message": "ModelPlay AI API Server is running"}


@app.get("/docs")
async def docs():
    return {"message": "API documentation available at /docs or /redoc"}


if __name__ == "__main__":
    import uvicorn
    init_components()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
