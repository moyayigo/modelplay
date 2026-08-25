"""ModelPlay 应用开发模板
保留 # !!! 标记的框架代码，替换 # >>> 标记的部分。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
import streamlit as st
import requests, json
from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

# ============ 配置 ============
API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()  # !!! 必须 > 后端 timeout
GAME_TYPE = "my_app"  # >>> 应用类型
GAME_META = {"title": "My App", "icon": "🎮", "description": "Description"}  # >>>
GAME_PROMPT = """(Rules description, must specify the JSON format returned by the model)"""  # >>>
# !!! game_prompt 只要求模型返回动作（如出招、坐标、答案）
# !!! 如果应用类型是 "game"，则在前端判定胜负、描述结果（这些在前端实现）

# ============ 页面配置 ============
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
st.set_page_config(page_title=GAME_META["title"], page_icon=GAME_META["icon"], layout="centered")
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# ============ 状态初始化 ============
_defaults = {"session_id": None, "status": "not_started", "game_log": [],
             "final_result": None, "game_summary": None, "attempt_count": 0,
             "pending_action": None, "last_model_action": None}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
# >>> 添加应用特有状态（如目标数字、比分、棋盘等）

# ============ 辅助函数 ============
def add_log(msg, is_user=True):
    st.session_state.game_log.append(("👤" if is_user else "🤖", msg))

def parse_model_action(data):
    """解析模型响应，兼容 dict/str 两种格式。"""
    action = data.get("action") or data.get("move_data")
    if isinstance(action, dict):
        return action
    if isinstance(action, str):
        try:
            return json.loads(action)
        except (json.JSONDecodeError, ValueError):
            return None
    return None

# ============ 控制函数 ============
def start_game():
    try:
        resp = requests.post(f"{API_BASE_URL}/api/game/start",
                             json={"game_type": GAME_TYPE, "game_prompt": GAME_PROMPT},
                             timeout=30)
        resp.raise_for_status()
        st.session_state.session_id = resp.json()["session_id"]
        st.session_state.status = "playing"
        for k in _defaults:
            if k not in ("session_id", "status"):
                st.session_state[k] = _defaults[k]
        # >>> 在前端生成游戏状态（!!! 不能从后端获取，用 random.randint()）
        add_log("🎮 App started", is_user=False)
    except requests.exceptions.RequestException as e:
        st.error(f"Startup failed: {str(e)}")

def make_action(user_action):
    """Send user action, get model response (with 3 retries). Returns True on success."""
    req = {"session_id": st.session_state.session_id, "player": "user",  # !!! 只能是 "user"
           "action": user_action, "board": {"state": None, "turn": "model"},  # >>> 替换为实际状态
           "status": "playing"}
    for attempt in range(3):
        try:
            resp = requests.post(f"{API_BASE_URL}/api/game/move",
                                 json=req, timeout=FRONTEND_TIMEOUT)
            resp.raise_for_status()
            model_action = parse_model_action(resp.json())
            if model_action is None:
                if attempt < 2:
                    continue
                break
            # >>> 验证模型动作合法性，非法则修改 req["action"] 为 retry prompt 并 continue
            st.session_state["last_model_action"] = model_action  # !!! 保存供 UI 展示
            add_log(f"Model response: {model_action}", is_user=False)
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
            return False
    st.session_state.status = "ended"
    st.session_state.final_result = "Multiple invalid model responses"
    add_log("😵 Model continuously returned invalid responses, game over", is_user=False)
    return False

def get_summary():
    try:
        resp = requests.post(f"{API_BASE_URL}/api/game/summary/{st.session_state.session_id}",
                             timeout=FRONTEND_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("strategic_analysis", "No summary available")
    except requests.exceptions.RequestException:
        return "Summary generation failed"

def reset_game():
    for k, v in _defaults.items():
        st.session_state[k] = v
    # >>> 重置其他应用特有状态

# ============ UI ============
if st.session_state.status == "not_started":
    # >>> 开始界面
    st.markdown(f"# {GAME_META['icon']} {GAME_META['title']}")
    st.write(GAME_META["description"])
    if st.button("Start", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    # >>> Game interface
    st.write(f"Round: {st.session_state.attempt_count + 1}")

    # !!! 按钮触发模式：点击 → 存 session_state → rerun 后处理
    options = [("Option A", "a"), ("Option B", "b"), ("Option C", "c")]  # >>> Replace with actual options
    cols = st.columns(len(options))
    for col, (label, value) in zip(cols, options):
        if col.button(label, use_container_width=True):
            st.session_state["pending_action"] = value  # !!! 存入 session_state

    # !!! 处理待执行的用户动作
    if st.session_state.get("pending_action"):
        user_move = st.session_state.pop("pending_action")  # !!! 取出并清除
        st.session_state.attempt_count += 1
        add_log(f"You chose: {user_move}", is_user=True)
        # !!! 调用 make_action 获取模型动作（不要自己写 requests.post）
        success = make_action({"type": "move", "value": user_move})
        if success:
            # !!! 如果应用类型是 "game"，则在前端判定胜负（!!! 不要让模型判定，模型只负责出招）
            model_resp = st.session_state.get("last_model_action", {})
            ai_move = model_resp.get("move", "")  # >>> 只取模型动作字段
            # >>> 自己实现胜负判定：result = judge(user_move, ai_move)    
            # >>> 更新比分、检查胜利条件
        st.rerun()

    # >>> 展示上一次的结果
    last = st.session_state.get("last_model_action")
    if last:
        st.info(f"AI response: {last}")
    # >>> Display game state (score, board, history, etc.)

elif st.session_state.status == "ended":
    # >>> End screen
    st.write(st.session_state.final_result or "Ended")
    if st.session_state.game_summary is not None:
        st.info(st.session_state.game_summary)
    elif st.button("Generate summary"):
        st.session_state.game_summary = get_summary()
        st.rerun()
    if st.button("Restart", type="primary"):
        reset_game()
        st.rerun()

# ============ Sidebar ============
with st.sidebar:
    st.header("📋 Log")
    for icon, msg in reversed(st.session_state.game_log):
        st.write(f"{icon} {msg}")
    if st.session_state.session_id:
        st.caption(f"Session ID: {st.session_state.session_id}")