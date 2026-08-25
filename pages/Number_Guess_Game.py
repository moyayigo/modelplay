import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import requests, json
import random
from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(page_title="Number Guessing Game", page_icon="🔢", layout="centered", initial_sidebar_state="auto")
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "status" not in st.session_state:
    st.session_state.status = "not_started"
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "final_result" not in st.session_state:
    st.session_state.final_result = None
if "current_player" not in st.session_state:
    st.session_state.current_player = "user"
if "target_number" not in st.session_state:
    st.session_state.target_number = None
if "guess_count" not in st.session_state:
    st.session_state.guess_count = 0
if "pending_guess" not in st.session_state:
    st.session_state.pending_guess = None
if "game_summary" not in st.session_state:
    st.session_state.game_summary = None


def add_log(message, is_user=True):
    color = "#3498db" if is_user else "#e74c3c"
    icon = "👤" if is_user else "🤖"
    st.session_state.game_log.append({"message": message, "color": color, "icon": icon})


def start_game():
    game_prompt = (
        "You are an AI assistant in a number guessing game."
        "Game rules: The system generates a random integer from 1-100, and the user and AI take turns guessing."
        "After each guess, determine if it's correct. If not, provide a hint of 'too high' or 'too low' based on the relationship between the guess and the target."
        "You need to use a binary search strategy based on previous guesses and feedback."
        "Return JSON format: {\"player\": \"assistant\", \"guess\": number}"
    )
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/game/start",
            json={"game_type": "number_guess", "game_prompt": game_prompt},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        st.session_state.session_id = data.get("session_id")
        st.session_state.status = "playing"
        st.session_state.target_number = random.randint(1, 100)
        st.session_state.guess_count = 0
        st.session_state.game_log = []
        st.session_state.current_player = "user"
        st.session_state.final_result = None
        st.session_state.game_summary = None
        add_log(f"🎮 Game started! Random number generated, current turn: Player", is_user=False)
    except Exception as e:
        st.error(f"Startup failed: {str(e)}")


def make_user_guess(guess):
    if st.session_state.current_player != "user":
        return

    target = st.session_state.target_number
    if target is None:
        st.error("Game state error: target number not set. Please restart the game.")
        st.session_state.status = "not_started"
        st.rerun()
        return
    guess = int(guess)
    st.session_state.guess_count += 1

    if guess == target:
        add_log(f"🎉 Player guessed it! Answer is {target}", is_user=True)
        st.session_state.status = "ended"
        st.session_state.final_result = f"Player wins! Answer is {target}"
        return

    feedback = "Too high!" if guess > target else "Too low!"
    add_log(f"Player guesses: {guess} - {feedback}", is_user=True)
    st.session_state.current_player = "model"

    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {"type": "guess", "value": guess, "feedback": feedback},
        "board": {
            "state": {"last_guess": guess, "feedback": feedback, "target_hint": "hidden"},
            "turn": "model",
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
            if isinstance(model_action, str):
                import re
                match = re.search(r'\{[\s\S]*\}', model_action)
                if match:
                    model_action = json.loads(match.group())
                else:
                    model_action = {"guess": 50}

            if isinstance(model_action, dict):
                ai_guess = model_action.get("guess", 50)
            elif isinstance(model_action, (list, tuple)) and len(model_action) >= 1:
                ai_guess = model_action[0]
            else:
                ai_guess = 50

            try:
                ai_guess = int(ai_guess)
            except (TypeError, ValueError):
                ai_guess = 50

            ai_guess = max(1, min(100, ai_guess))
            st.session_state.guess_count += 1

            if ai_guess == target:
                add_log(f"🤖 AI guessed it! Answer is {target}", is_user=False)
                st.session_state.status = "ended"
                st.session_state.final_result = f"AI wins! Answer is {target}"
                return

            ai_feedback = "Too high!" if ai_guess > target else "Too low!"
            add_log(f"🤖 AI guesses: {ai_guess} - {ai_feedback}", is_user=False)
            st.session_state.current_player = "user"
            return

        except Exception as e:
            if attempt < 2:
                continue
            add_log(f"⚠️ AI guess failed: {str(e)}", is_user=False)
            st.session_state.current_player = "user"

    st.session_state.current_player = "user"


def reset_game():
    st.session_state.status = "not_started"
    st.session_state.session_id = None
    st.session_state.game_log = []
    st.session_state.final_result = None
    st.session_state.current_player = "user"
    st.session_state.target_number = None
    st.session_state.guess_count = 0
    st.session_state.pending_guess = None
    st.session_state.game_summary = None
    st.rerun()


# ================= UI =================
st.title("🔢 Number Guessing Game")
st.markdown("You and AI take turns guessing a number from 1-100, whoever guesses correctly first wins!")

if st.session_state.status == "not_started":
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <div style="font-size:64px; margin-bottom:20px;">🔢🎯</div>
        <p style="color:#a0a0a0;">Take turns guessing with AI, first to guess correctly wins</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Game", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    current = "👤 Player" if st.session_state.current_player == "user" else "🤖 AI"
    st.info(f"Current turn: {current} | Guess count: {st.session_state.guess_count}")

    if st.session_state.current_player == "user":
        guess = st.number_input("Enter your guess (1-100)", min_value=1, max_value=100, value=50, key="guess_input")
        if st.button("Submit Guess", type="primary", use_container_width=True):
            make_user_guess(guess)
            st.rerun()
    else:
        with st.spinner("🤖 AI is thinking..."):
            pass

elif st.session_state.status == "ended":
    final = st.session_state.final_result or ""
    if "Player" in final:
        st.success(f"🎉 {final}")
    else:
        st.error(f"😢 {final}")

    st.markdown(f"**Total Guesses**: {st.session_state.guess_count}")

    if st.session_state.game_summary is not None:
        st.markdown("---")
        st.subheader("📊 Match Summary")
        st.info(st.session_state.game_summary)
    elif st.button("🤖 Generate Match Summary", use_container_width=True):
        with st.spinner("Generating..."):
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
                st.error(f"Generation failed: {str(e)}")

    if st.button("Restart", type="primary", use_container_width=True):
        reset_game()

# ================= Sidebar =================
with st.sidebar:
    st.header("📋 Game Log")
    if st.session_state.game_log:
        for log in reversed(st.session_state.game_log):
            with st.expander(
                f"{log['icon']} {log['message'][:60]}{'...' if len(log['message']) > 60 else ''}",
                expanded=False,
            ):
                st.markdown(
                    f"<div style='color:{log['color']}; padding:4px;'>"
                    f"<pre style='white-space: pre-wrap; margin:0; font-size:13px;'>{log['message']}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No logs yet")

    if st.session_state.session_id:
        st.divider()
        st.caption(f"Session ID: {st.session_state.session_id}")
