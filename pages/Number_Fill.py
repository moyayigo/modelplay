import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json

from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()

GAME_PROMPTS = {
    "number_fill": """You are playing a number-filling game with the user.

Game rules:
1. Players take turns filling in integers between 1-100
2. Each filled number must be different from all previously filled numbers
3. Your goal is to choose a number different from the user's
4. The return format must be JSON: {"player": "assistant", "move": X}, where X is an integer from 1-100""",
}

GAME_TYPE = "number_fill"

GAME_META = {
    "title": "Number Fill Game",
    "icon": "🔢",
    "description": "Play number-filling game against AI, fill in different numbers to discover patterns.",
}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(
    page_title="Number Fill Game",
    page_icon="🔢",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

st.title("🔢 Number Fill Game")
st.markdown("Take turns filling in numbers from 1-100 with the AI model")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "state" not in st.session_state:
    st.session_state.state = None
if "turn" not in st.session_state:
    st.session_state.turn = "user"
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "status" not in st.session_state:
    st.session_state.status = "not_started"
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {"last_request": None, "last_response": None, "last_error": None}
if "show_debug" not in st.session_state:
    st.session_state.show_debug = False
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "final_result" not in st.session_state:
    st.session_state.final_result = None
if "game_summary" not in st.session_state:
    st.session_state.game_summary = None


def add_log(message, is_user=True):
    color = "#3498db" if is_user else "#e74c3c"
    icon = "👤" if is_user else "🤖"
    st.session_state.game_log.append({"message": message, "color": color, "icon": icon})


def start_game():
    game_prompt = GAME_PROMPTS.get(GAME_TYPE, "")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/game/start",
            json={"game_type": GAME_TYPE, "game_prompt": game_prompt},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        st.session_state.session_id = data["session_id"]
        st.session_state.state = None
        st.session_state.turn = "user"
        st.session_state.status = "playing"
        st.session_state.game_log = []

        add_log(f"🎮 Game started, session ID: {data['session_id']}", is_user=False)
        if game_prompt:
            add_log(f"📋 Game rules:\n{game_prompt}", is_user=False)
        add_log("It's your turn! Please enter a number from 1-100", is_user=False)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start game: {str(e)}")


def make_action(user_action):
    if st.session_state.turn != "model":
        st.warning("State error")
        return False

    if isinstance(user_action, (int, float)) and (user_action < 1 or user_action > 100):
        st.error("Please enter a number between 1-100")
        return False

    st.session_state.debug_info["last_error"] = None
    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": user_action,
        "board": {"state": user_action, "turn": "model"},
        "status": "playing",
    }
    st.session_state.debug_info["last_request"] = request_data

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/game/move",
            json=request_data,
            timeout=FRONTEND_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        st.session_state.debug_info["last_response"] = data
        print(f"[Frontend Debug] Received response: {data}")

        model_action = data.get("action")
        # Extract the actual number from model response for display
        if isinstance(model_action, dict):
            move = model_action.get("move")
            if move is None:
                move = model_action.get("action")
            st.session_state.state = move if move is not None else model_action
        else:
            st.session_state.state = model_action
        st.session_state.turn = "user"

        add_log(f"Model response: {model_action}", is_user=False)

        if data.get("message"):
            add_log(f"💬 {data['message']}", is_user=False)

        if model_action is None:
            add_log("⚠️ Model failed to return a valid action", is_user=False)

        return True

    except requests.exceptions.Timeout:
        error_msg = f"⏱️ Timeout ({FRONTEND_TIMEOUT} seconds), model is thinking, please retry later"
        st.session_state.debug_info["last_error"] = error_msg
        st.session_state.turn = "user"
        add_log(f"❌ {error_msg}", is_user=False)
        return False
    except requests.exceptions.ConnectionError:
        error_msg = "🔗 Cannot connect to server, please ensure the backend service is running"
        st.session_state.debug_info["last_error"] = error_msg
        st.session_state.turn = "user"
        add_log(f"❌ {error_msg}", is_user=False)
        return False
    except requests.exceptions.HTTPError as e:
        error_msg = f"❌ HTTP Error: {e.response.status_code} - {e.response.text}"
        st.session_state.debug_info["last_error"] = error_msg
        st.session_state.turn = "user"
        add_log(f"❌ {error_msg}", is_user=False)
        return False
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to send request: {str(e)}"
        st.session_state.debug_info["last_error"] = error_msg
        st.session_state.turn = "user"
        add_log(f"❌ {error_msg}", is_user=False)
        return False


def end_game():
    if st.session_state.session_id:
        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/game/end/{st.session_state.session_id}",
                timeout=10,
            )
            data = resp.json()
            st.session_state.final_result = data.get("result")
        except:
            pass

        st.session_state.status = "ended"
        add_log("🏁 Game over", is_user=False)
        if st.session_state.state is not None:
            add_log(f"Final state: {st.session_state.state}", is_user=False)


if st.session_state.status == "not_started":
    if st.button("Start Game", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.state is not None:
            state_display = st.session_state.state
            if isinstance(state_display, (dict, list)):
                state_display = json.dumps(state_display, ensure_ascii=False, indent=2)
            st.markdown(
                f"<h1 style='text-align: center; color: {st.session_state.game_log[-1]['color'] if st.session_state.game_log else '#3498db'}'>"
                f"{state_display}</h1>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<h1 style='text-align: center; color: #95a5a6'>?</h1>",
                unsafe_allow_html=True,
            )

    with col2:
        if st.session_state.turn == "user":
            number_input = st.number_input(
                "Enter number",
                min_value=1,
                max_value=100,
                step=1,
                key="number_input",
            )
            if st.button("Confirm", key="confirm_btn"):
                st.session_state.state = number_input
                st.session_state.turn = "model"
                st.session_state.pending_action = number_input
                add_log(f"You filled in: {number_input}", is_user=True)
                st.rerun()
        else:
            st.write("Model is thinking...")

    if st.session_state.turn == "model" and st.session_state.pending_action is not None:
        action = st.session_state.pending_action
        st.session_state.pending_action = None
        with st.spinner("Model is thinking..."):
            success = make_action(action)
        if success:
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Game Log")
    log_container = st.container()
    with log_container:
        for i, log in enumerate(st.session_state.game_log):
            with st.expander(f"{log['icon']} {log['message'][:60]}{'...' if len(log['message']) > 60 else ''}", expanded=False):
                st.markdown(
                    f"<div style='color:{log['color']}; padding: 4px;'>"
                    f"<pre style='white-space: pre-wrap; margin: 0;'>{log['message']}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if st.button("End Game", use_container_width=True, key="end_btn"):
        end_game()
        st.rerun()

elif st.session_state.status == "ended":
    st.markdown(
        f"<h1 style='text-align: center; color: #95a5a6'>🏁</h1>",
        unsafe_allow_html=True,
    )
    if st.session_state.final_result is not None:
        result = st.session_state.final_result
        if isinstance(result, (dict, list)):
            result = json.dumps(result, ensure_ascii=False, indent=2)
        st.subheader(f"Final Result: {result}")

    if st.session_state.game_summary is not None:
        st.markdown("---")
        st.subheader("Match Summary")
        st.info(st.session_state.game_summary)
    elif st.button("🤖 Generate Match Summary", use_container_width=True):
        with st.spinner("Generating match summary..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/api/game/summary/{st.session_state.session_id}",
                    timeout=FRONTEND_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.game_summary = data.get("strategic_analysis", "Generation failed")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate summary: {str(e)}")

    st.markdown("---")
    st.subheader("📋 Game Log")
    log_container = st.container()
    with log_container:
        for log in st.session_state.game_log:
            with st.expander(f"{log['icon']} {log['message'][:60]}{'...' if len(log['message']) > 60 else ''}", expanded=False):
                st.markdown(
                    f"<div style='color:{log['color']}; padding: 4px;'>"
                    f"<pre style='white-space: pre-wrap; margin: 0;'>{log['message']}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if st.button("Restart", use_container_width=True):
        st.session_state.status = "not_started"
        st.session_state.game_summary = None
        st.rerun()

with st.sidebar:
    st.header("🔧 Debug Panel")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Check Connection", use_container_width=True):
            try:
                resp = requests.get(f"{API_BASE_URL}/", timeout=5)
                st.success("✅ Server Online")
            except Exception as e:
                st.error("✅ Cannot Connect")
                st.code(str(e))

    with col2:
        if st.button("View Docs", use_container_width=True):
            try:
                docs_url = f"{API_BASE_URL}/docs"
                st.info(f"📖 API Docs: {docs_url}")
            except:
                pass

    st.divider()
    st.subheader("⚙️ Configuration")
    st.info(f"API URL: {API_BASE_URL}")
    st.info(f"Request Timeout: {FRONTEND_TIMEOUT}s")
    st.info(f"Game Type: {GAME_TYPE}")

    st.divider()
    st.subheader("Session Status")
    state_display = st.session_state.state
    if isinstance(state_display, (dict, list)):
        state_display = json.dumps(state_display, ensure_ascii=False)
    st.json({
        "session_id": st.session_state.session_id,
        "state": state_display,
        "turn": st.session_state.turn,
        "status": st.session_state.status,
        "log_count": len(st.session_state.game_log),
    })

    st.divider()
    st.subheader("Debug Info")
    show_debug = st.checkbox("Show debug info", value=st.session_state.show_debug)
    st.session_state.show_debug = show_debug

    if show_debug and st.session_state.debug_info.get("last_request"):
        st.text("📤 Last Request")
        st.json(st.session_state.debug_info["last_request"])

    if show_debug and st.session_state.debug_info.get("last_response"):
        st.text("📦 Last Response")
        resp = st.session_state.debug_info["last_response"]
        if isinstance(resp, dict):
            display_resp = {k: v for k, v in resp.items()}
            st.json(display_resp)

    if st.session_state.debug_info.get("last_error"):
        st.error(f"❌ {st.session_state.debug_info['last_error']}")
    else:
        st.success("✅ No Errors")
