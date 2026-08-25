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
    page_title="AI 应用构建器",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

st.title("🛠️ AI 应用构建器")
st.caption("描述你想构建的应用，AI 将为你生成符合 ModelPlay 框架的完整代码")

FRAMEWORK_KNOWLEDGE = """你是 ModelPlay 框架的资深开发者。请根据用户需求生成完整的 Streamlit 应用代码。

## 框架架构
- 前端：Streamlit 单页应用（pages/目录下的 .py 文件）
- 后端：FastAPI (api_server.py)，通过 HTTP REST API 通信
- 通信：前端用 requests 库调用后端 API

## API 端点
1. POST /api/game/start — 请求：{game_type, game_prompt} → 响应：{session_id}
2. POST /api/game/move — 请求：{session_id, player:"user", action, board, status} → 响应：{session_id, player:"assistant", action, board, status, message}
3. POST /api/game/summary/{session_id} — 返回 {strategic_analysis}
4. 响应中 action 字段可为 dict 或 str，需兼容两种格式

## 三种应用类型
1. 游戏 (game): 用户 vs AI 对抗，turn 交替，胜负判定后结束
2. 课程 (course): AI 作为引导者主动提问，学生回答，AI 评估反馈
3. 协同 (collaborative): 人机共建产物，用户反馈 accept/reject/edit

## ⚠️ 三条绝对规则（违反会导致运行错误）
1. **目标数字/答案必须在前端用 random.randint() 生成**，后端只返回 session_id
   - ❌ target = data.get("target_number")  # 会变成 None
   - ❌ None > int 会报 TypeError
2. **只发送 player:"user" 的请求**，后端自动调用模型并返回响应
   - ❌ 绝不能发送 player:"assistant"
3. **game_prompt 必须明确要求模型返回 JSON 格式**，否则模型返回自然语言无法解析

## 代码模板
生成代码时，**必须严格基于下面的模板结构填充**，不要重写整个文件，不要改变整体结构。模板内容见下方 _template 字段。

## 输出要求
返回严格的 JSON：
{
    "app_name": "应用英文标识",
    "app_title": "中文标题",
    "app_icon": "emoji图标",
    "app_type": "game|course|collaborative",
    "file_name": "保存的文件名（不含.py）",
    "description": "功能描述",
    "game_prompt": "发给模型的系统提示词（必须指定返回JSON格式）",
    "code": "完整的 Python 文件内容（基于模板填充）",
    "features": ["功能1", "功能2", ...]
}
"""


# 加载开发模板（src/temple.py）作为代码生成的骨架参考
def _load_template():
    """读取 src/temple.py 模板内容，供代码生成阶段参考。"""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src/temple_zh.py",
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
    "gathering": "1. 需求收集",
    "designing": "2. 方案设计",
    "coding": "3. 代码生成",
    "reviewing": "4. 预览修改",
    "saving": "5. 保存完成",
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
        add_log(f"🎯 需求已提交: {requirement_text[:60]}", is_user=False)
    except Exception as e:
        st.error(f"启动构建器失败: {str(e)}")


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
            "_design_hint": "\n\n请返回 JSON 格式设计方案，包含 app_name, app_title, app_icon, app_type, description, features 字段。注意：应用设计中app_type为game时，不要让模型判断胜负，模型只负责出招，胜负逻辑写在前端，不要输出类似result这样含义的字段。"
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
                add_log("📐 方案设计完成", is_user=False)

                # 如果模型在 design 阶段已经返回了 code，保存为备用
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
                    add_log("💾 设计阶段已包含代码（已保存为备用）", is_user=False)
                return
            else:
                if attempt < 2:
                    continue

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"设计失败: {str(e)}")

    st.warning("设计超时，请重试")


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
                "\n\n请基于上方 _template 模板生成代码。\n"
                "规则：\n"
                "1. 严格保留标记为 `# !!!` 的框架代码，原样不动\n"
                "2. 只替换标记为 `# >>>` 的游戏特定部分（GAME_TYPE、GAME_PROMPT、GAME_META、游戏状态、胜负判定等）\n"
                "3. 不要重写整个文件，不要改变整体结构\n"
                "4. 必须包含完整可运行的代码（基于模板填充）\n\n"
                "返回严格的 JSON 格式：\n"
                "{\n"
                '  "app_name": "英文标识",\n'
                '  "app_title": "中文标题",\n'
                '  "app_icon": "emoji",\n'
                '  "app_type": "game|course|collaborative",\n'
                '  "file_name": "文件名（不含.py）",\n'
                '  "description": "描述",\n'
                '  "game_prompt": "给模型的系统提示词（必须指定返回JSON格式）",\n'
                '  "code": "完整的 Python 代码（基于模板填充）",\n'
                '  "features": ["功能列表"]\n'
                "}\n\n"
                "⚠️ 绝对禁止：\n"
                "- 从后端获取 target_number（后端只返回 session_id）\n"
                "- 发送 player:\"assistant\" 请求\n"
                "- game_prompt 不指定 JSON 返回格式\n"
                "- None 和 int 比较"
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
                add_log("❌ JSON 解析全部失败", is_user=False)
                break

            # 递归查找 code 字段（兼容嵌套结构如 response.code、data.code）
            code_value = _find_field_recursive(parsed, "code")

            if code_value is not None and isinstance(code_value, str) and len(code_value) > 50:
                st.session_state.generated_code = code_value
                # 同样递归查找其他元数据字段
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
                add_log(f"💻 代码生成完成: {st.session_state.app_metadata.get('file_name', 'MyApp')}.py", is_user=False)
                return
            else:
                if attempt < 2:
                    continue
                if code_value is None:
                    add_log(f"❌ 响应缺少 code 字段（可用: {', '.join(list(parsed.keys())[:4])}...）", is_user=False)
                else:
                    add_log(f"❌ code 字段无效（长度={len(str(code_value))}）", is_user=False)

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"代码生成失败: {str(e)}")

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
                add_log("💻 代码生成完成（回退模式：从代码块提取）", is_user=False)
                return

    # Fallback 2: use code saved from design phase if available
    if st.session_state.generated_code and len(st.session_state.generated_code) > 50:
        st.session_state.builder_phase = "reviewing"
        add_log("💻 使用设计阶段已生成的代码", is_user=False)
        return

    st.warning("代码生成失败，请重试或调整需求描述")


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
            "_code_hint": "\n\n请返回修改后的完整 JSON，包含 code 字段（完整 Python 代码）和其他元数据字段。",
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
                # 递归查找 code 字段（兼容嵌套结构）
                code_value = _find_field_recursive(parsed, "code")
                if code_value is not None and isinstance(code_value, str) and len(code_value) > 50:
                    st.session_state.generated_code = code_value
                    # 递归更新元数据
                    for meta_key in ("app_title", "app_name", "file_name"):
                        meta_val = _find_field_recursive(parsed, meta_key)
                        if meta_val is not None:
                            st.session_state.app_metadata[meta_key] = meta_val
                    add_log("✏️ 代码已根据反馈修改", is_user=False)
                    return
            else:
                if attempt < 2:
                    continue

        except Exception as e:
            if attempt < 2:
                continue
            st.error(f"修改失败: {str(e)}")

    # Fallback for revision too
    if isinstance(model_action, str):
        code_blocks = re.findall(r'```python\s*\n(.*?)```', model_action, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'```\s*\n(.*?)```', model_action, re.DOTALL)
        if code_blocks:
            best_code = max(code_blocks, key=len)
            if len(best_code) > 50:
                st.session_state.generated_code = best_code
                add_log("✏️ 从代码块提取修改（回退模式）", is_user=False)
                return

    st.warning("修改超时")


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
        st.error(f"语法错误，保存失败: {e}")
        return False

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        st.session_state.saved_file = file_path
        st.session_state.builder_phase = "saving"
        add_log(f"💾 已保存到 pages/{safe_name}.py", is_user=False)
        return True
    except Exception as e:
        st.error(f"保存失败: {str(e)}")
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
    st.caption(f"📋 当前阶段: {PHASES.get(current_phase, current_phase)}")

st.markdown("---")

if st.session_state.builder_phase == "gathering":
    st.markdown("### 🎯 第 1 步：描述你想构建的应用")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        requirement = st.text_area(
            "📝 描述你的应用需求",
            height=120,
            placeholder="例如：一个双人对战的石头剪刀布游戏，玩家选择石头/剪刀/布，AI 随机出招并判定胜负（注意：复杂控制需要描述按钮或按键的功能）。",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            app_type = st.selectbox(
                "🏷️ 应用类型",
                ["game", "course", "collaborative"],
                format_func=lambda x: {"game": "🎮 游戏", "course": "📚 课程", "collaborative": "🤝 协同"}[x],
            )
        with col_b:
            target_user = st.selectbox(
                "👥 目标用户",
                ["children", "teenagers", "adults", "professionals"],
                format_func=lambda x: {"children": "👶 儿童", "teenagers": "🧒 青少年", "adults": "👨 成人", "professionals": "💼 专业人士"}[x],
            )

        features = st.multiselect(
            "✨ 功能特性",
            ["score_tracking", "progress_bar", "timer", "levels", "achievements", "share", "rules"],
            format_func=lambda x: {
                "score_tracking": "📊 分数追踪",
                "progress_bar": "📈 进度条",
                "timer": "⏱️ 计时器",
                "levels": "🏆 关卡系统",
                "achievements": "🎖️ 成就系统",
                "share": "📤 分享功能",
                "rules": "📝 规则系统",
            }[x],
        )

    with col_right:
        st.markdown("#### 💡 提示")
        st.info(
            "描述越具体，生成的应用越符合预期：\n\n"
            "- **游戏**: 规则、玩法、胜负条件\n"
            "- **课程**: 主题、难度、评估方式\n"
            "- **协同**: 任务类型、交互方式"
        )

        #existing = check_existing_pages()
        #if existing:
        #    st.markdown("#### 📁 现有页面")
        #    for f in existing:
        #        st.caption(f"  • {f}")

    if st.button("🚀 生成方案", type="primary", use_container_width=True):
        if requirement:
            start_builder(requirement, app_type, features, target_user)
            st.rerun()
        else:
            st.warning("请先描述你的应用需求")

elif st.session_state.builder_phase == "designing":
    st.markdown("### 📐 第 2 步：AI 正在设计方案...")

    reqs = st.session_state.user_requirements
    with st.expander("📋 你的需求", expanded=True):
        st.markdown(f"**需求**: {reqs['requirement']}")
        st.markdown(f"**类型**: {reqs['app_type']}")
        st.markdown(f"**目标用户**: {reqs['target_user']}")
        st.markdown(f"**特性**: {', '.join(reqs['features'])}")

    if st.button("✨ 生成设计方案", type="primary", use_container_width=True):
        with st.spinner("AI 正在分析需求并设计方案..."):
            request_design()
        st.rerun()

elif st.session_state.builder_phase == "coding":
    st.markdown("### 💻 第 3 步：AI 正在生成代码...")

    design = st.session_state.app_design
    if design:
        with st.expander("📐 设计方案", expanded=True):
            st.json(design)

    if st.button("🚀 生成代码", type="primary", use_container_width=True):
        with st.spinner("AI 正在编写完整的 Streamlit 应用代码..."):
            request_code()
        st.rerun()

elif st.session_state.builder_phase == "reviewing":
    st.markdown("### 🔍 第 4 步：预览和修改")

    metadata = st.session_state.app_metadata
    code = st.session_state.generated_code

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.metric("📱 应用名称", metadata.get("app_title", ""))
    with col_meta2:
        st.metric("🏷️ 类型", metadata.get("app_type", ""))
    with col_meta3:
        st.metric("📁 文件名", f"{metadata.get('file_name', '')}.py")
    with col_meta4:
        features = metadata.get("features", [])
        st.metric("✨ 功能数", len(features))

    if metadata.get("description"):
        st.markdown(f"**📝 描述**: {metadata['description']}")

    if features:
        st.markdown("**✨ 功能**: " + ", ".join(features))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 代码预览", "✏️ 代码编辑"])

    with tab1:
        st.code(code, language="python")

    with tab2:
        edited_code = st.text_area(
            "直接编辑代码",
            value=code,
            height=500,
            key="code_editor",
        )
        if st.button("✅ 应用修改", type="primary", use_container_width=True):
            try:
                compile(edited_code, "preview.py", "exec")
                st.session_state.generated_code = edited_code
                add_log("✏️ 代码已手动编辑", is_user=True)
                st.success("✅ 语法正确，修改已应用")
                st.rerun()
            except SyntaxError as e:
                st.error(f"❌ 语法错误: {e}")

    st.markdown("---")

    col_revise, col_save = st.columns([1, 2])
    with col_revise:
        revision_feedback = st.text_area(
            "💬 请求 AI 修改",
            placeholder="描述你希望 AI 如何修改，例如：把棋盘改成 4x4、增加计时功能...",
            height=80,
            key="revision_feedback",
        )
        if st.button("🔄 请 AI 修改", use_container_width=True):
            if revision_feedback:
                with st.spinner("AI 正在根据反馈修改代码..."):
                    request_code_revision(revision_feedback)
                st.rerun()

    with col_save:
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in metadata.get("file_name", "MyApp"))
        if not safe_name[0].isalpha():
            safe_name = "App_" + safe_name
        st.markdown(f"**💾 保存路径**: `pages/{safe_name}.py`")

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.button("💾 保存到 pages/", type="primary", use_container_width=True):
                with st.spinner("正在保存..."):
                    success = save_to_pages()
                if success:
                    st.rerun()
        with col_save2:
            if st.button("🧪 验证语法", use_container_width=True):
                try:
                    compile(code, f"{safe_name}.py", "exec")
                    st.success("✅ 语法检查通过！")
                except SyntaxError as e:
                    st.error(f"❌ 语法错误: {e}")

elif st.session_state.builder_phase == "saving":
    st.markdown("### ✅ 第 5 步：保存完成！")

    saved = st.session_state.saved_file
    metadata = st.session_state.app_metadata
    file_name = os.path.basename(saved) if saved else "unknown.py"

    st.markdown("---")

    col_success1, col_success2, col_success3 = st.columns([1, 2, 1])
    with col_success2:
        st.markdown(
            f"<div style='text-align:center; padding:30px; background:rgba(46,213,115,0.1); border-radius:15px;'>"
            f"<div style='font-size:64px;'>🎉</div>"
            f"<h2 style='color:#2ecc71;'>构建成功！</h2>"
            f"<p>你的应用已保存到: <code>pages/{file_name}</code></p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📱 应用", metadata.get("app_title", ""))
    with col2:
        st.metric("🏷️ 类型", metadata.get("app_type", ""))
    with col3:
        st.metric("📁 文件", file_name)

    st.markdown("---")

    with st.expander("📝 完整代码", expanded=False):
        st.code(st.session_state.generated_code, language="python")

    st.markdown("---")
    col_restart, col_goto = st.columns([1, 1])
    with col_restart:
        if st.button("🔄 构建另一个", use_container_width=True):
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
        st.markdown("💡 **下一步**: 刷新 Streamlit 页面，新应用将出现在 pages 列表中。")
        st.caption("然后在 game_hub 或侧边栏中点击即可运行。")

# ================= 侧边栏 =================
with st.sidebar:
    st.header("📋 构建日志")
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
        st.caption("暂无日志")

    if st.session_state.session_id:
        st.divider()
        st.caption(f"会话ID: {st.session_state.session_id}")

    st.divider()
    st.subheader("📊 构建进度")
    for phase_key, phase_name in PHASES.items():
        status = "✅" if list(PHASES.keys()).index(phase_key) < list(PHASES.keys()).index(st.session_state.builder_phase) else "⏳"
        if phase_key == st.session_state.builder_phase:
            status = "👉"
        st.markdown(f"{status} {phase_name}")

    existing = check_existing_pages()
    if existing:
        st.divider()
        st.subheader("📁 现有页面")
        for f in existing:
            st.caption(f"  • {f}")
