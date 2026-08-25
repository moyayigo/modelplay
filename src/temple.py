"""ModelPlay Application Development Template
Keep the framework code marked with # !!!, replace the parts marked with # >>>.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
import streamlit as st
import requests, json
from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

# ============ Configuration ============
API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()  # !!! must be > backend timeout
GAME_TYPE = "my_app"  # >>> Application type
GAME_META = {"title": "My App", "icon": "🎮", "description": "Description"}  # >>>
GAME_PROMPT = """(Rules description, must specify the JSON format returned by the model)"""  # >>>
# !!! game_prompt only requires the model to return an action (e.g., move, coordinate, answer)
# !!! If the application type is "game", judge win/loss and describe results on the frontend (these are implemented on the frontend)

# ============ Page Configuration ============
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
st.set_page_config(page_title=GAME_META["title"], page_icon=GAME_META["icon"], layout="centered")
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# ============ State Initialization ============
_defaults = {"session_id": None, "status": "not_started", "game_log": [],
             "final_result": None, "game_summary": None, "attempt_count": 0,
             "pending_action": None, "last_model_action": None}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
# >>> Add application-specific state (e.g., target number, score, board, etc.)

# ============ Helper Functions ============
def add_log(msg, is_user=True):
    st.session_state.game_log.append(("👤" if is_user else "🤖", msg))

def parse_model_action(data):
    """Parse model response, compatible with both dict/str formats."""
    action = data.get("action") or data.get("move_data")
    if isinstance(action, dict):
        return action
    if isinstance(action, str):
        try:
            return json.loads(action)
        except (json.JSONDecodeError, ValueError):
            return None
    return None

# ============ Control Functions ============
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
        # >>> Generate game state on the frontend (!!! cannot get from backend, use random.randint())
        add_log("🎮 App started", is_user=False)
    except requests.exceptions.RequestException as e:
        st.error(f"Startup failed: {str(e)}")

def make_action(user_action):
    """Send user action, get model response (with 3 retries). Returns True on success."""
    req = {"session_id": st.session_state.session_id, "player": "user",  # !!! must be "user"
           "action": user_action, "board": {"state": None, "turn": "model"},  # >>> Replace with actual state
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
            # >>> Validate model action legality; if invalid, modify req["action"] to a retry prompt and continue
            st.session_state["last_model_action"] = model_action  # !!! Save for UI display
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
    # >>> Reset other application-specific state

# ============ UI ============
if st.session_state.status == "not_started":
    # >>> Start screen
    st.markdown(f"# {GAME_META['icon']} {GAME_META['title']}")
    st.write(GAME_META["description"])
    if st.button("Start", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    # >>> Game interface
    st.write(f"Round: {st.session_state.attempt_count + 1}")

    # !!! Button trigger mode: click → save to session_state → process after rerun
    options = [("Option A", "a"), ("Option B", "b"), ("Option C", "c")]  # >>> Replace with actual options
    cols = st.columns(len(options))
    for col, (label, value) in zip(cols, options):
        if col.button(label, use_container_width=True):
            st.session_state["pending_action"] = value  # !!! Save to session_state

    # !!! Process pending user action
    if st.session_state.get("pending_action"):
        user_move = st.session_state.pop("pending_action")  # !!! Retrieve and clear
        st.session_state.attempt_count += 1
        add_log(f"You chose: {user_move}", is_user=True)
        # !!! Call make_action to get the model action (do not write requests.post yourself)
        success = make_action({"type": "move", "value": user_move})
        if success:
            # !!! If the application type is "game", judge win/loss on the frontend (!!! do not let the model judge; the model is only responsible for moves)
            model_resp = st.session_state.get("last_model_action", {})
            ai_move = model_resp.get("move", "")  # >>> Only extract the model action field
            # >>> Implement win/loss judgment yourself: result = judge(user_move, ai_move)
            # >>> Update scores, check win conditions
        st.rerun()

    # >>> Display the last result
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
