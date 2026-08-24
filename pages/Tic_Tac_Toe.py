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

GAME_TYPE = "tic_tac_toe"

GAME_PROMPTS = {
    "tic_tac_toe": """You are playing Tic-Tac-Toe with the user.

Game rules:
1. You play as "O", the user plays as "X"
2. The board is a 3x3 grid, indexed by row 0-2, col 0-2
3. Take turns placing your mark
4. First to connect three in a line (horizontal, vertical, or diagonal) wins
5. If all 9 cells are filled with no winner, it's a draw

Your task:
- Analyze the current board state
- Choose the best placement for "O"
- Prioritize winning moves, then block opponent's winning moves
- Return format must be JSON: {"player": "assistant", "row": X, "col": Y}
  where row and col are integers from 0-2""",
}

GAME_META = {
    "title": "Tic-Tac-Toe",
    "icon": "⭕",
    "description": "Play Tic-Tac-Toe against AI, first to connect three in a line wins",
}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(
    page_title="Tic-Tac-Toe",
    page_icon="⭕",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

BOARD_CSS = """
<style>
div[data-testid="stButton"] button[kind="primary"] {
    aspect-ratio: 1 / 1 !important;
    width: 100% !important;
    height: auto !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 42px !important;
    font-weight: bold !important;
    line-height: 1 !important;
    background-color: #ffffff !important;
    color: #262730 !important;
    border: 3px solid #d3d3d3 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] button[kind="primary"] p {
    font-size: 42px !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover:not(:disabled) {
    background-color: #f0f8ff !important;
    border-color: #ff4b4b !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
}
div[data-testid="stButton"] button[kind="primary"]:disabled {
    background-color: #f8f9fa !important;
    color: #262730 !important;
    border-color: #e0e0e0 !important;
    cursor: not-allowed !important;
    opacity: 1 !important;
    transform: none !important;
    box-shadow: none !important;
}
</style>
"""
st.markdown(BOARD_CSS, unsafe_allow_html=True)

st.title("⭕ Tic-Tac-Toe")
st.markdown("You play ❌, AI plays ⭕. First to connect three in a line wins!")

# ================= 状态管理 =================
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "board" not in st.session_state:
    st.session_state.board = [["" for _ in range(3)] for _ in range(3)]
if "turn" not in st.session_state:
    st.session_state.turn = "user"
if "status" not in st.session_state:
    st.session_state.status = "not_started"
if "winner" not in st.session_state:
    st.session_state.winner = None
if "is_draw" not in st.session_state:
    st.session_state.is_draw = False
if "game_log" not in st.session_state:
    st.session_state.game_log = []
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


def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != "":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != "":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != "":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != "":
        return board[0][2]
    return None


def check_draw(board):
    return all(cell != "" for row in board for cell in row)


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
        st.session_state.board = [["" for _ in range(3)] for _ in range(3)]
        st.session_state.turn = "user"
        st.session_state.status = "playing"
        st.session_state.winner = None
        st.session_state.is_draw = False
        st.session_state.game_log = []

        add_log(f"🎮 Game started, session ID: {data['session_id']}", is_user=False)
        if game_prompt:
            add_log(f"📋 Game rules:\n{game_prompt}", is_user=False)
        add_log("It's your turn! Please select a cell to place ❌", is_user=False)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start game: {str(e)}")


def get_empty_cells(board):
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == ""]


def make_action(user_row, user_col):
    if st.session_state.turn != "model":
        st.warning("State error")
        return False

    board = st.session_state.board
    empty_cells_before = get_empty_cells(board)

    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {"row": user_row, "col": user_col, "mark": "X"},
        "board": {"state": board, "turn": "model"},
        "status": "playing",
    }

    available_str = ", ".join([f"({r},{c})" for r, c in empty_cells_before])
    retry_prompt = (
        f"\n\nIMPORTANT: The cells {available_str} are currently empty. "
        f"You MUST choose one of these empty cells for your move. "
        f"Do NOT pick an already-occupied cell. "
        f"Return ONLY the JSON format: {{\"player\": \"assistant\", \"row\": X, \"col\": Y}}"
    )

    max_attempts = 3
    for attempt in range(max_attempts):
        prompt_extra = retry_prompt if attempt > 0 else ""
        if attempt > 0:
            add_log(f"🔄 Retry attempt {attempt}, informed model of available cells", is_user=False)

        current_request = dict(request_data)
        if prompt_extra:
            current_request["action"] = {
                "row": user_row, "col": user_col, "mark": "X",
                "_retry_hint": prompt_extra,
            }

        st.session_state.debug_info["last_request"] = current_request

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/game/move",
                json=current_request,
                timeout=FRONTEND_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            st.session_state.debug_info["last_response"] = data
            print(f"[Frontend Debug] Received response (attempt {attempt+1}): {data}")

            model_action = data.get("action")

            if model_action is None:
                add_log("⚠️ Model failed to return a valid action", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            if isinstance(model_action, dict):
                model_row = model_action.get("row")
                model_col = model_action.get("col")
            elif isinstance(model_action, (list, tuple)) and len(model_action) >= 2:
                model_row, model_col = model_action[0], model_action[1]
            else:
                add_log(f"⚠️ Model returned format error: {model_action}", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            try:
                model_row = int(model_row)
                model_col = int(model_col)
            except (TypeError, ValueError):
                add_log(f"⚠️ Model coordinates invalid: row={model_row}, col={model_col}", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            if model_row < 0 or model_row > 2 or model_col < 0 or model_col > 2:
                add_log(f"⚠️ Model coordinates out of bounds: row={model_row}, col={model_col}", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            if board[model_row][model_col] != "":
                add_log(
                    f"⚠️ Model selected occupied cell: ({model_row}, {model_col})."
                    f"Available cells: {available_str}",
                    is_user=False,
                )
                if attempt < max_attempts - 1:
                    continue
                break

            board[model_row][model_col] = "O"
            st.session_state.board = board
            st.session_state.turn = "user"

            add_log(f"Model response: ({model_row}, {model_col}) ⭕", is_user=False)

            if check_winner(board):
                st.session_state.winner = "O"
                st.session_state.status = "ended"
                add_log("😢 AI wins!", is_user=False)
            elif check_draw(board):
                st.session_state.is_draw = True
                st.session_state.status = "ended"
                add_log("🤝 Draw!", is_user=False)

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

    add_log(
        f"😵 Model continuously made {max_attempts} invalid moves, game forced to end.",
        is_user=False,
    )
    st.session_state.turn = "user"
    st.session_state.status = "ended"
    st.session_state.is_draw = True
    st.session_state.final_result = {
        "reason": "Model made multiple invalid moves, game auto-ended",
    }
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


# ================= Game UI =================
if st.session_state.status == "not_started":
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <div style="font-size:64px; margin-bottom:20px;">⭕❌</div>
        <p style="color:#a0a0a0; margin-bottom:28px;">Play Tic-Tac-Toe against AI, AI plays ⭕, you play ❌</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Game", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    board = st.session_state.board

    if st.session_state.winner:
        if st.session_state.winner == "X":
            st.success("🎉 **You (❌)** Win!")
        else:
            st.error("😢 AI (⭕) Wins!")
    elif st.session_state.is_draw:
        st.warning("🤝 Draw!")
    else:
        current_player = "❌ You" if st.session_state.turn == "user" else "⭕ AI"
        st.info(f"Current turn: {current_player}")

    # Draw board
    left_spacer, board_area, right_spacer = st.columns([1, 3, 1])
    with board_area:
        for i in range(3):
            cols = st.columns(3)
            for j in range(3):
                cell_value = board[i][j]
                disabled = st.session_state.turn != "user" or cell_value != ""

                if cell_value == "X":
                    label = "❌"
                elif cell_value == "O":
                    label = "⭕"
                else:
                    label = " "

                if cols[j].button(
                    label,
                    key=f"cell_{i}_{j}",
                    disabled=disabled,
                    use_container_width=True,
                    type="primary",
                ):
                    if st.session_state.turn == "user" and cell_value == "":
                        board = st.session_state.board
                        board[i][j] = "X"
                        st.session_state.board = board
                        add_log(f"You placed: ({i}, {j}) ❌", is_user=True)
                        st.session_state.pending_action = (i, j)
                        st.session_state.turn = "model"
                        st.rerun()

    if st.session_state.pending_action is not None:
        action = st.session_state.pending_action
        st.session_state.pending_action = None

        board = st.session_state.board
        if check_winner(board) == "X":
            st.session_state.winner = "X"
            st.session_state.status = "ended"
            add_log("🎉 You win!", is_user=True)
            st.rerun()
        elif check_draw(board):
            st.session_state.is_draw = True
            st.session_state.status = "ended"
            add_log("🤝 Draw!", is_user=False)
            st.rerun()
        else:
            with st.spinner("Model is thinking..."):
                success = make_action(action[0], action[1])
            if success or st.session_state.status == "ended":
                st.rerun()

    if st.button("End Game", use_container_width=True, key="end_btn"):
        end_game()
        st.rerun()

elif st.session_state.status == "ended":
    if st.session_state.winner:
        if st.session_state.winner == "X":
            st.success("🎉 **You (❌)** Win!")
        else:
            st.error("😢 AI (⭕) Wins!")
    elif st.session_state.is_draw:
        if st.session_state.final_result and isinstance(st.session_state.final_result, dict) and "reason" in st.session_state.final_result:
            st.warning("😵 Game forced to end")
            st.info(st.session_state.final_result["reason"])
        else:
            st.warning("🤝 Draw!")

    board = st.session_state.board
    left_spacer, board_area, right_spacer = st.columns([1, 3, 1])
    with board_area:
        for i in range(3):
            cols = st.columns(3)
            for j in range(3):
                cell_value = board[i][j]
                label = cell_value if cell_value else " "
                cols[j].button(label, key=f"final_{i}_{j}", disabled=True, use_container_width=True, type="primary")

    if st.session_state.game_summary is not None:
        st.markdown("---")
        st.subheader("📊 Match Summary")
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

    if st.button("Restart", use_container_width=True):
        st.session_state.status = "not_started"
        st.session_state.board = [["" for _ in range(3)] for _ in range(3)]
        st.session_state.turn = "user"
        st.session_state.winner = None
        st.session_state.is_draw = False
        st.session_state.game_log = []
        st.session_state.final_result = None
        st.session_state.game_summary = None
        st.rerun()

# ================= Sidebar: Game Log =================
with st.sidebar:
    st.header("📋 Game Log")
    if st.session_state.game_log:
        for log in reversed(st.session_state.game_log):
            with st.expander(
                f"{log['icon']} {log['message'][:50]}{'...' if len(log['message']) > 50 else ''}",
                expanded=False,
            ):
                st.markdown(
                    f"<div style='color:{log['color']}; padding: 4px;'>"
                    f"<pre style='white-space: pre-wrap; margin: 0; font-size:13px;'>{log['message']}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No logs yet")

    if st.session_state.session_id:
        st.divider()
        st.caption(f"Session ID: {st.session_state.session_id}")