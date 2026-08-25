import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
import re

from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()

BUILDER_TYPE = "app_builder"

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(
    page_title="AI App Builder",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

st.title("🛠️ AI App Builder")
st.caption("Describe the app you want to build, AI will generate complete code conforming to the ModelPlay framework")

FRAMEWORK_KNOWLEDGE = """You are a senior developer of the ModelPlay framework. Please generate complete Streamlit application code based on user requirements.

## Framework Architecture
- Frontend: Streamlit single-page application (.py files in pages/ directory)
- Backend: FastAPI (api_server.py), communicates via HTTP REST API
- Communication: Frontend calls backend API using requests library

## API Endpoints
1. POST /api/game/start — Request: {game_type, game_prompt} → Response: {session_id}
2. POST /api/game/move — Request: {session_id, player:"user", action, board, status} → Response: {session_id, player:"assistant", action, board, status, message}
3. POST /api/game/summary/{session_id} — Returns {strategic_analysis}
4. The action field in the response can be dict or str, both formats need to be compatible

## Three Application Types
1. Game: User vs AI confrontation, turns alternate, ends after win/loss determination
2. Course: AI acts as guide asking questions proactively, students answer, AI evaluates and provides feedback
3. Collaborative: Human and AI co-create products, user provides accept/reject/edit feedback

## ⚠️ Three Absolute Rules (violations will cause runtime errors)
1. **Target number/answer MUST be generated on the frontend using random.randint()**, backend only returns session_id
   - ❌ target = data.get("target_number")  # Will become None
   - ❌ None > int will cause TypeError
2. **Only send requests with player:"user"**, backend automatically calls the model and returns response
   - ❌ NEVER send player:"assistant"
3. **game_prompt MUST explicitly require the model to return JSON format**, otherwise the model returns natural language which cannot be parsed

## Code Template
When generating code, you **MUST strictly fill in based on the template structure below**, do not rewrite the entire file, do not change the overall structure. Template content is in the _template field below.

## Output Requirements
Return strict JSON:
{
    "app_name": "App English identifier",
    "app_title": "English title",
    "app_icon": "emoji icon",
    "app_type": "game|course|collaborative",
    "file_name": "Saved file name (without .py)",
    "description": "Feature description",
    "game_prompt": "System prompt sent to model (must specify return JSON format)",
    "code": "Complete Python file content (filled based on template)",
    "features": ["Feature 1", "Feature 2", ...]
}
"""


# 加载开发模板（src/temple.py）作为代码生成的骨架参考
def _load_template():
    """读取 src/temple.py 模板内容，供代码生成阶段参考。"""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src/temple.py",
    )
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, OSError):
        return ""


if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "builder_phase" not in st.session_state:
    st.session_state.builder_phase = "gathering"
if "user_requirements" not in st.session_state:
    st.session_state.user_requirements = {}
if "app_design" not in st.session_state:
    st.session_state.app_design = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None
if "app_metadata" not in st.session_state:
    st.session_state.app_metadata = None
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "saved_file" not in st.session_state:
    st.session_state.saved_file = None
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {}

PHASES = {
    "gathering": "1. Requirement Gathering",
    "designing": "2. Design",
    "coding": "3. Code Generation",
    "reviewing": "4. Preview & Edit",
    "saving": "5. Save Complete",
}


def add_log(message, is_user=True):
    color = "#3498db" if is_user else "#e74c3c"
    icon = "👤" if is_user else "🤖"
    st.session_state.game_log.append({"message": message, "color": color, "icon": icon})


def _robust_parse_response(model_action):
    if isinstance(model_action, dict):
        return model_action
    if not isinstance(model_action, str):
        return None

    text = model_action.strip()

    # 1. Try direct JSON parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code blocks and try again
    stripped = re.sub(r'^```(?:json)?\s*\n?', '', text)
    stripped = re.sub(r'\n?```\s*$', '', stripped)
    stripped = stripped.strip()
    if stripped != text:
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    # 3. Find the first { and try JSONDecoder.raw_decode
    for i, ch in enumerate(text):
        if ch == '{':
            try:
                obj, _ = json.JSONDecoder().raw_decode(text[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                break

    # 4. Find last complete JSON block using brace matching
    brace_positions = []
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string and ch == '{':
            brace_positions.append(i)

    for pos in reversed(brace_positions):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[pos:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    return None


def _find_field_recursive(obj, target_key, max_depth=4):
    """递归查找目标字段，遍历所有嵌套 dict 层。"""
    if max_depth <= 0:
        return None
    if not isinstance(obj, dict):
        return None
    if target_key in obj:
        value = obj[target_key]
        if value is not None:
            return value
    # 遍历所有嵌套的 dict 值进行递归查找
    for key, value in obj.items():
        if isinstance(value, dict):
            found = _find_field_recursive(value, target_key, max_depth - 1)
            if found is not None:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = _find_field_recursive(item, target_key, max_depth - 1)
                    if found is not None:
                        return found
    return None


def start_builder(requirement_text, app_type, features, target_user):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/game/start",
            json={
                "game_type": BUILDER_TYPE,
                "game_prompt": FRAMEWORK_KNOWLEDGE,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        st.session_state.session_id = data["session_id"]
        st.session_state.user_requirements = {
            "requirement": requirement_text,
            "app_type": app_type,
            "features": features,
            "target_user": target_user,
        }
        st.session_state.builder_phase = "designing"
        add_log(f"🎯 Requirements submitted: {requirement_text[:60]}", is_user=False)
    except Exception as e:
        st.error(f"Failed to start builder: {str(e)}")


def request_design():
    if st.session_state.session_id is None:
        return

    reqs = st.session_state.user_requirements
    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {
            "type": "design_request",
            "requirement": reqs["requirement"],
            "app_type": reqs["app_type"],
            "features": reqs["features"],
            "target_user": reqs["target_user"],
            "_design_hint": "\n\nPlease return a JSON format design proposal, including app_name, app_title, app_icon, app_type, description, features fields. Note: When the app_type in the app design is game, do not let the model judge win/loss, the model is only responsible for making moves, the win/loss logic is written on the frontend, do not output fields with meanings like result."
        },
        "board": {
            "state": "designing",
            "turn": "model",
            "phase": "design",
        },
        "status": "playing",
    }

    for attempt in range(3):
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/game/move",
                json=request_data,
                timeout=FRONTEND_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            model_action = data.get("action")
            parsed = _robust_parse_response(model_action)

            if parsed is not None:
                # 优先使用嵌套的 response 字段（模型常用此结构）
                design_data = _find_field_recursive(parsed, "app_name")
                if design_data is not None:
                    # 找到嵌套的设计对象，提取它
                    for key in ("response", "data", "result"):
                        if key in parsed and isinstance(parsed[key], dict):
                            if "app_name" in parsed[key] or "description" in parsed[key]:
                                parsed = parsed[key]
                                break
                st.session_state.app_design = parsed
                st.session_state.builder_phase = "coding"
                add_log("📐 Design plan completed", is_user=False)

                # If the model has already returned code in the design phase, save as backup
                early_code = _find_field_recursive(parsed, "code")
                if early_code is not None and isinstance(early_code, str) and len(early_code) > 50:
                    st.session_state.generated_code = early_code
                    def _get_meta_design(key, default=""):
                        val = _find_field_recursive(parsed, key)
                        return val if val is not None else default
                    st.session_state.app_metadata = {
                        "app_name": _get_meta_design("app_name", "MyApp"),
                        "app_title": _get_meta_design("app_title", "My App"),
                        "app_icon": _get_meta_design("app_icon", "📱"),
                        "app_type": _get_meta_design("app_type", reqs["app_type"]),
                        "file_name": _get_meta_design("file_name", "MyApp"),
                        "description": _get_meta_design("description", ""),
                        "features": _get_meta_design("features", []) or [],
                    }
                    add_log("💾 Code already included in design phase (saved as backup)", is_user=False)
                return
            else:
                if attempt < 2:
                    continue

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"Design failed: {str(e)}")

    st.warning("Design timed out, please retry")


def request_code():
    if st.session_state.session_id is None:
        return

    design = st.session_state.app_design
    reqs = st.session_state.user_requirements

    # 加载开发模板，作为代码生成的骨架参考
    template_content = _load_template()

    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {
            "type": "code_request",
            "requirement": reqs["requirement"],
            "app_type": reqs["app_type"],
            "design_summary": json.dumps(design, ensure_ascii=False) if design else "",
            "_template": template_content,
            "_code_hint": (
                "\n\nPlease generate code based on the _template template above.\n"
                "Rules:\n"
                "1. Strictly preserve the framework code marked with `# !!!`, keep it unchanged\n"
                "2. Only replace the game-specific parts marked with `# >>>` (GAME_TYPE, GAME_PROMPT, GAME_META, game state, win/loss determination, etc.)\n"
                "3. Do not rewrite the entire file, do not change the overall structure\n"
                "4. Must include complete runnable code (filled based on template)\n\n"
                "Return strict JSON format:\n"
                "{\n"
                '  "app_name": "English identifier",\n'
                '  "app_title": "English title",\n'
                '  "app_icon": "emoji",\n'
                '  "app_type": "game|course|collaborative",\n'
                '  "file_name": "file name (without .py)",\n'
                '  "description": "description",\n'
                '  "game_prompt": "system prompt to model (must specify return JSON format)",\n'
                '  "code": "complete Python code (filled based on template)",\n'
                '  "features": ["feature list"]\n'
                "}\n\n"
                "⚠️ Strictly prohibited:\n"
                "- Getting target_number from backend (backend only returns session_id)\n"
                "- Sending player:\"assistant\" requests\n"
                "- game_prompt not specifying JSON return format\n"
                "- Comparing None with int"
            ),
        },
        "board": {
            "state": "coding",
            "turn": "model",
            "phase": "code",
            "design": design,
        },
        "status": "playing",
    }

    last_raw_response = None

    for attempt in range(3):
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/game/move",
                json=request_data,
                timeout=FRONTEND_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            model_action = data.get("action")
            last_raw_response = model_action

            parsed = _robust_parse_response(model_action)

            if parsed is None:
                if attempt < 2:
                    continue
                add_log("❌ All JSON parsing failed", is_user=False)
                break

            # Recursively find the code field (compatible with nested structures like response.code, data.code)
            code_value = _find_field_recursive(parsed, "code")

            if code_value is not None and isinstance(code_value, str) and len(code_value) > 50:
                st.session_state.generated_code = code_value
                # Also recursively find other metadata fields
                def _get_meta(key, default=""):
                    val = _find_field_recursive(parsed, key)
                    return val if val is not None else default
                st.session_state.app_metadata = {
                    "app_name": _get_meta("app_name", "MyApp"),
                    "app_title": _get_meta("app_title", "My App"),
                    "app_icon": _get_meta("app_icon", "📱"),
                    "app_type": _get_meta("app_type", reqs["app_type"]),
                    "file_name": _get_meta("file_name", "MyApp"),
                    "description": _get_meta("description", ""),
                    "features": _get_meta("features", []) or [],
                }
                st.session_state.builder_phase = "reviewing"
                add_log(f"💻 Code generation complete: {st.session_state.app_metadata.get('file_name', 'MyApp')}.py", is_user=False)
                return
            else:
                if attempt < 2:
                    continue
                if code_value is None:
                    add_log(f"❌ Response missing code field (available: {', '.join(list(parsed.keys())[:4])}...）", is_user=False)
                else:
                    add_log(f"❌ code field invalid (length={len(str(code_value))})", is_user=False)

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"Code generation failed: {str(e)}")

    # Fallback 1: try to extract code blocks from raw response
    if last_raw_response and isinstance(last_raw_response, str):
        code_blocks = re.findall(r'```python\s*\n(.*?)```', last_raw_response, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'```\s*\n(.*?)```', last_raw_response, re.DOTALL)
        if code_blocks:
            best_code = max(code_blocks, key=len)
            if len(best_code) > 50:
                st.session_state.generated_code = best_code
                if not st.session_state.app_metadata:
                    st.session_state.app_metadata = {
                        "app_name": reqs.get("app_type", "MyApp").title(),
                        "app_title": "Generated App",
                        "app_icon": "📱",
                        "app_type": reqs.get("app_type", "game"),
                        "file_name": "MyApp",
                        "description": reqs.get("requirement", ""),
                        "features": reqs.get("features", []),
                    }
                st.session_state.builder_phase = "reviewing"
                add_log("💻 Code generation complete (fallback mode: extracted from code block)", is_user=False)
                return

    # Fallback 2: use code saved from design phase if available
    if st.session_state.generated_code and len(st.session_state.generated_code) > 50:
        st.session_state.builder_phase = "reviewing"
        add_log("💻 Using code generated in design phase", is_user=False)
        return

    st.warning("Code generation failed, please retry or adjust requirement description")


def request_code_revision(feedback):
    if st.session_state.session_id is None:
        return

    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {
            "type": "code_revision",
            "feedback": feedback,
            "current_code": st.session_state.generated_code,
            "_code_hint": "\n\nPlease return the modified complete JSON, including the code field (complete Python code) and other metadata fields.",
        },
        "board": {
            "state": "revising",
            "turn": "model",
            "phase": "revision",
        },
        "status": "playing",
    }

    for attempt in range(3):
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/game/move",
                json=request_data,
                timeout=FRONTEND_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            model_action = data.get("action")
            parsed = _robust_parse_response(model_action)

            if parsed:
                # Recursively find the code field (compatible with nested structures)
                code_value = _find_field_recursive(parsed, "code")
                if code_value is not None and isinstance(code_value, str) and len(code_value) > 50:
                    st.session_state.generated_code = code_value
                    # Recursively update metadata
                    for meta_key in ("app_title", "app_name", "file_name"):
                        meta_val = _find_field_recursive(parsed, meta_key)
                        if meta_val is not None:
                            st.session_state.app_metadata[meta_key] = meta_val
                    add_log("✏️ Code has been modified based on feedback", is_user=False)
                    return
            else:
                if attempt < 2:
                    continue

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"Modification failed: {str(e)}")

    # Fallback for revision too
    if isinstance(model_action, str):
        code_blocks = re.findall(r'```python\s*\n(.*?)```', model_action, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'```\s*\n(.*?)```', model_action, re.DOTALL)
        if code_blocks:
            best_code = max(code_blocks, key=len)
            if len(best_code) > 50:
                st.session_state.generated_code = best_code
                add_log("✏️ Extracted modification from code block (fallback mode)", is_user=False)
                return

    st.warning("Modification timed out")


def save_to_pages():
    metadata = st.session_state.app_metadata
    code = st.session_state.generated_code
    file_name = metadata.get("file_name", "MyApp")

    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in file_name)
    if not safe_name[0].isalpha():
        safe_name = "App_" + safe_name

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "pages",
        f"{safe_name}.py",
    )

    try:
        compile(code, file_path, "exec")
    except SyntaxError as e:
        st.error(f"Syntax error, save failed: {e}")
        return False

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        st.session_state.saved_file = file_path
        st.session_state.builder_phase = "saving"
        add_log(f"💾 Saved to pages/{safe_name}.py", is_user=False)
        return True
    except Exception as e:
        st.error(f"Save failed: {str(e)}")
        return False


def check_existing_pages():
    pages_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "pages",
    )
    try:
        files = [f for f in os.listdir(pages_dir) if f.endswith(".py") and not f.startswith("_")]
        return sorted(files)
    except:
        return []


# ================= Builder UI =================

col_phase, col_info = st.columns([1, 3])
with col_phase:
    current_phase = st.session_state.builder_phase
    phase_num = list(PHASES.keys()).index(current_phase) + 1 if current_phase in PHASES else 1
    st.progress(phase_num / len(PHASES))
with col_info:
    st.caption(f"📋 Current phase: {PHASES.get(current_phase, current_phase)}")

st.markdown("---")

if st.session_state.builder_phase == "gathering":
    st.markdown("### 🎯 Step 1: Describe the app you want to build")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        requirement = st.text_area(
            "📝 Describe your app requirements",
            height=120,
            placeholder="e.g., A two-player rock-paper-scissors game where players choose rock/paper/scissors, AI randomly plays and determines winner (note: complex controls need to be described in detail^^).",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            app_type = st.selectbox(
                "🏷️ App Type",
                ["game", "course", "collaborative"],
                format_func=lambda x: {"game": "🎮 Game", "course": "📚 Course", "collaborative": "🤝 Collaborative"}[x],
            )
        with col_b:
            target_user = st.selectbox(
                "👥 Target Users",
                ["children", "teenagers", "adults", "professionals"],
                format_func=lambda x: {"children": "👶 Children", "teenagers": "🧒 Teenagers", "adults": "👨 Adults", "professionals": "💼 Professionals"}[x],
            )

        features = st.multiselect(
            "✨ Features",
            ["score_tracking", "progress_bar", "timer", "levels", "achievements", "share", "rules"],
            format_func=lambda x: {
                "score_tracking": "📊 Score Tracking",
                "progress_bar": "📈 Progress Bar",
                "timer": "⏱️ Timer",
                "levels": "🏆 Level System",
                "achievements": "🎖️ Achievement System",
                "share": "📤 Share Feature",
                "rules": "📝 Rule System",
            }[x],
        )

    with col_right:
        st.markdown("#### 💡 Tips")
        st.info(
            "The more specific the description, the better the generated app will match expectations:\n\n"
            "- **Game**: Rules, gameplay, win/loss conditions\n"
            "- **Course**: Topic, difficulty, assessment method\n"
            "- **Collaborative**: Task type, interaction method"
        )

        #existing = check_existing_pages()
        #if existing:
        #    st.markdown("#### 📁 Existing Pages")
        #    for f in existing:
        #        st.caption(f"  • {f}")

    if st.button("🚀 Generate Plan", type="primary", use_container_width=True):
        if requirement:
            start_builder(requirement, app_type, features, target_user)
            st.rerun()
        else:
            st.warning("Please describe your app requirements first")

elif st.session_state.builder_phase == "designing":
    st.markdown("### 📐 Step 2: AI is designing the plan...")

    reqs = st.session_state.user_requirements
    with st.expander("📋 Your Requirements", expanded=True):
        st.markdown(f"**Requirement**: {reqs['requirement']}")
        st.markdown(f"**Type**: {reqs['app_type']}")
        st.markdown(f"**Target Users**: {reqs['target_user']}")
        st.markdown(f"**Features**: {', '.join(reqs['features'])}")

    if st.button("✨ Generate Design Plan", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing requirements and designing plan..."):
            request_design()
        st.rerun()

elif st.session_state.builder_phase == "coding":
    st.markdown("### 💻 Step 3: AI is generating code...")

    design = st.session_state.app_design
    if design:
        with st.expander("📐 Design Plan", expanded=True):
            st.json(design)

    if st.button("🚀 Generate Code", type="primary", use_container_width=True):
        with st.spinner("AI is writing complete Streamlit app code..."):
            request_code()
        st.rerun()

elif st.session_state.builder_phase == "reviewing":
    st.markdown("### 🔍 Step 4: Preview and Edit")

    metadata = st.session_state.app_metadata
    code = st.session_state.generated_code

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.metric("📱 App Name", metadata.get("app_title", ""))
    with col_meta2:
        st.metric("🏷️ Type", metadata.get("app_type", ""))
    with col_meta3:
        st.metric("📁 File Name", f"{metadata.get('file_name', '')}.py")
    with col_meta4:
        features = metadata.get("features", [])
        st.metric("✨ Feature Count", len(features))

    if metadata.get("description"):
        st.markdown(f"**📝 Description**: {metadata['description']}")

    if features:
        st.markdown("**✨ Features**: " + ", ".join(features))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 Code Preview", "✏️ Code Edit"])

    with tab1:
        st.code(code, language="python")

    with tab2:
        edited_code = st.text_area(
            "Edit code directly",
            value=code,
            height=500,
            key="code_editor",
        )
        if st.button("✅ Apply Changes", type="primary", use_container_width=True):
            try:
                compile(edited_code, "preview.py", "exec")
                st.session_state.generated_code = edited_code
                add_log("✏️ Code manually edited", is_user=True)
                st.success("✅ Syntax correct, changes applied")
                st.rerun()
            except SyntaxError as e:
                st.error(f"❌ Syntax error: {e}")

    st.markdown("---")

    col_revise, col_save = st.columns([1, 2])
    with col_revise:
        revision_feedback = st.text_area(
            "💬 Request AI Modification",
            placeholder="Describe how you want AI to modify, e.g., change board to 4x4, add timer...",
            height=80,
            key="revision_feedback",
        )
        if st.button("🔄 Ask AI to Modify", use_container_width=True):
            if revision_feedback:
                with st.spinner("AI is modifying code based on feedback..."):
                    request_code_revision(revision_feedback)
                st.rerun()

    with col_save:
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in metadata.get("file_name", "MyApp"))
        if not safe_name[0].isalpha():
            safe_name = "App_" + safe_name
        st.markdown(f"**💾 Save Path**: `pages/{safe_name}.py`")

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.button("💾 Save to pages/", type="primary", use_container_width=True):
                with st.spinner("Saving..."):
                    success = save_to_pages()
                if success:
                    st.rerun()
        with col_save2:
            if st.button("🧪 Verify Syntax", use_container_width=True):
                try:
                    compile(code, f"{safe_name}.py", "exec")
                    st.success("✅ Syntax check passed!")
                except SyntaxError as e:
                    st.error(f"❌ Syntax error: {e}")

elif st.session_state.builder_phase == "saving":
    st.markdown("### ✅ Step 5: Save Complete!")

    saved = st.session_state.saved_file
    metadata = st.session_state.app_metadata
    file_name = os.path.basename(saved) if saved else "unknown.py"

    st.markdown("---")

    col_success1, col_success2, col_success3 = st.columns([1, 2, 1])
    with col_success2:
        st.markdown(
            f"<div style='text-align:center; padding:30px; background:rgba(46,213,115,0.1); border-radius:15px;'>"
            f"<div style='font-size:64px;'>🎉</div>"
            f"<h2 style='color:#2ecc71;'>Build successful!</h2>"
            f"<p>Your app has been saved to: <code>pages/{file_name}</code></p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📱 App", metadata.get("app_title", ""))
    with col2:
        st.metric("🏷️ Type", metadata.get("app_type", ""))
    with col3:
        st.metric("📁 File", file_name)

    st.markdown("---")

    with st.expander("📝 Complete Code", expanded=False):
        st.code(st.session_state.generated_code, language="python")

    st.markdown("---")
    col_restart, col_goto = st.columns([1, 1])
    with col_restart:
        if st.button("🔄 Build Another", use_container_width=True):
            st.session_state.builder_phase = "gathering"
            st.session_state.user_requirements = {}
            st.session_state.app_design = None
            st.session_state.generated_code = None
            st.session_state.app_metadata = None
            st.session_state.saved_file = None
            st.session_state.game_log = []
            st.session_state.session_id = None
            st.rerun()
    with col_goto:
        st.markdown("💡 **Next Step**: Refresh the Streamlit page, the new app will appear in the pages list.")
        st.caption("Then click it in game_hub or sidebar to run.")

# ================= Sidebar =================
with st.sidebar:
    st.header("📋 Build Log")
    if st.session_state.game_log:
        for log in reversed(st.session_state.game_log):
            with st.expander(
                f"{log.get('icon', '📄') if isinstance(log, dict) else '📄'} {log.get('message', '')[:60] if isinstance(log, dict) else str(log)[:60]}{'...' if (len(log.get('message', '') if isinstance(log, dict) else str(log)) > 60) else ''}",
                expanded=False,
            ):
                st.markdown(
                    f"<div style='color:{log.get('color', '') if isinstance(log, dict) else '#2ecc71'}; padding:4px;'>"
                    f"<pre style='white-space: pre-wrap; margin:0; font-size:13px;'>{log.get('message', '') if isinstance(log, dict) else str(log) if isinstance(log, str) else log}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No logs yet")

    if st.session_state.session_id:
        st.divider()
        st.caption(f"Session ID: {st.session_state.session_id}")

    st.divider()
    st.subheader("📊 Build Progress")
    for phase_key, phase_name in PHASES.items():
        status = "✅" if list(PHASES.keys()).index(phase_key) < list(PHASES.keys()).index(st.session_state.builder_phase) else "⏳"
        if phase_key == st.session_state.builder_phase:
            status = "👉"
        st.markdown(f"{status} {phase_name}")

    existing = check_existing_pages()
    if existing:
        st.divider()
        st.subheader("📁 Existing Pages")
        for f in existing:
            st.caption(f"  • {f}")
