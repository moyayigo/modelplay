import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import chess

from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

API_BASE_URL = get_api_base_url()
FRONTEND_TIMEOUT = get_frontend_timeout()

GAME_TYPE = "chess"

GAME_PROMPTS = {
    "chess": """You are playing chess with the user.

Role: You play black pieces (lowercase r n b q k b n r p), the user plays white pieces (uppercase R N B Q K B N R P).

Board coordinates: columns a-h (left to right), rows 1-8 (white on rows 1-2, black on rows 7-8).

Move format: UCI notation, "from_square+to_square", e.g., "e2e4" (from e2 to e4), "g1f3" (knight from g1 to f3).

Special moves:
- Castling: short castle "e1g1" (white) or "e8g8" (black); long castle "e1c1" or "e8c8"
- Pawn promotion: when pawn reaches opponent's back rank, append the promotion piece letter, e.g., "e7e8q" (promote to queen), "a7a8r" (promote to rook)
- En passant: directly use from and to square coordinates

Key rules:
- Each move must be legal; you cannot leave your own king in check
- King cannot move to a square under attack
- Pawns move forward only, capture diagonally
- Knight (N) moves in L-shape, Bishop (B) moves diagonally, Rook (R) moves in straight lines, Queen (Q) moves any direction, King (K) moves one square

Your task:
- Analyze current board state
- Choose a legal move for black
- Return format must be JSON: {"move": "e7e5"}
  where move is a UCI format move string""",
}

GAME_META = {
    "title": "Chess",
    "icon": "♟️",
    "description": "Play chess against AI, checkmate the opponent's king to win",
}

PIECE_UNICODE = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(
    page_title="Chess",
    page_icon="♟️",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="stButton"] button[kind="primary"] {
    aspect-ratio: 1 / 1 !important;
    width: 100% !important;
    height: auto !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 38px !important;
    font-weight: normal !important;
    line-height: 1 !important;
    border-radius: 2px !important;
    border: 1px solid rgba(0,0,0,0.15) !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stButton"] button[kind="primary"] p {
    font-size: 38px !important;
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
    transform: scale(1.08) !important;
    z-index: 10 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}
div[data-testid="stButton"] button[kind="primary"]:disabled {
    opacity: 1 !important;
    cursor: default !important;
}
</style>
""", unsafe_allow_html=True)

st.title("♟️ Chess")
st.markdown("You play ♔ White, AI plays ♚ Black. Checkmate the opponent's king to win!")

# ================= 状态管理 =================
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "turn" not in st.session_state:
    st.session_state.turn = "user"
if "status" not in st.session_state:
    st.session_state.status = "not_started"
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "legal_targets" not in st.session_state:
    st.session_state.legal_targets = []
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {"last_request": None, "last_response": None, "last_error": None}
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "pending_promotion" not in st.session_state:
    st.session_state.pending_promotion = None
if "final_result" not in st.session_state:
    st.session_state.final_result = None
if "game_summary" not in st.session_state:
    st.session_state.game_summary = None


def add_log(message, is_user=True):
    color = "#3498db" if is_user else "#e74c3c"
    icon = "👤" if is_user else "🤖"
    st.session_state.game_log.append({"message": message, "color": color, "icon": icon})


def square_name(row, col):
    return chess.square_name(chess.square(col, 7 - row))


def get_piece_at(row, col):
    piece = st.session_state.board.piece_at(chess.square(col, 7 - row))
    return piece.symbol() if piece else ""


def get_legal_targets_for_square(sq_name):
    sq = chess.parse_square(sq_name)
    return [chess.square_name(m.to_square) for m in st.session_state.board.legal_moves if m.from_square == sq]


def board_to_visual():
    board = st.session_state.board
    lines = []
    ranks = ["8", "7", "6", "5", "4", "3", "2", "1"]
    lines.append("  a b c d e f g h")
    for i in range(8):
        rank_idx = 7 - i
        row_str = ranks[i] + " "
        for j in range(8):
            piece = board.piece_at(chess.square(j, rank_idx))
            row_str += (piece.symbol() if piece else ".") + " "
        lines.append(row_str)
    return "\n".join(lines)


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
        st.session_state.board = chess.Board()
        st.session_state.turn = "user"
        st.session_state.status = "playing"
        st.session_state.selected_square = None
        st.session_state.legal_targets = []
        st.session_state.game_log = []
        st.session_state.pending_promotion = None

        add_log(f"🎮 Game started, session ID: {data['session_id']}", is_user=False)
        add_log("It's your turn! Click a white piece to select a move", is_user=False)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start game: {str(e)}")


def make_action(user_move_uci):
    if st.session_state.turn != "model":
        st.warning("State error")
        return False

    board = st.session_state.board
    fen_before = board.fen()

    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": {"move": user_move_uci, "color": "white"},
        "board": {"state": fen_before, "turn": "model"},
        "status": "playing",
    }

    max_attempts = 3
    last_invalid_move = None
    last_error_reason = None

    for attempt in range(max_attempts):
        current_request = dict(request_data)
        if attempt > 0:
            legal_moves_uci = [m.uci() for m in board.legal_moves]
            visual = board_to_visual()
            retry_hint = (
                f"\n\nYour previous move \"{last_invalid_move}\" was illegal: {last_error_reason}."
                f"\n\nCurrent board state (FEN):\n{board.fen()}"
                f"\n\nVisual representation:\n{visual}"
                f"\n\nAll legal moves ({len(legal_moves_uci)} total):\n{', '.join(legal_moves_uci)}"
                f"\n\nPlease select one from the legal moves above, return JSON: {{\"move\": \"your chosen move\"}}"
            )
            current_request["action"] = {
                "move": user_move_uci,
                "color": "white",
                "_retry_hint": retry_hint,
            }
            add_log(f"🔄 Retry attempt {attempt}, {len(legal_moves_uci)} legal moves provided", is_user=False)

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
            print(f"[Frontend Debug] Response received (attempt {attempt+1}): {data}")

            model_action = data.get("action")
            model_move_str = None

            if isinstance(model_action, dict):
                model_move_str = model_action.get("move")
            elif isinstance(model_action, str):
                model_move_str = model_action
            else:
                last_invalid_move = str(model_action)
                last_error_reason = "Invalid return format, should be {\"move\": \"e2e4\"} format"
                add_log(f"⚠️ Model return format error: {model_action}", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            if not model_move_str:
                last_invalid_move = "(empty)"
                last_error_reason = "No valid move returned"
                add_log("⚠️ Model failed to return a valid move", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            model_move_str = model_move_str.strip().lower()

            try:
                move = board.parse_uci(model_move_str)
            except (ValueError, chess.InvalidMoveError) as e:
                last_invalid_move = model_move_str
                last_error_reason = str(e)[:80]
                add_log(
                    f"⚠️ Model move illegal: {model_move_str} (reason: {last_error_reason})",
                    is_user=False,
                )
                if attempt < max_attempts - 1:
                    continue
                break

            if move not in board.legal_moves:
                last_invalid_move = model_move_str
                last_error_reason = "Move not in legal moves list (may leave own king in check)"
                add_log(f"⚠️ Model move violation: {model_move_str}", is_user=False)
                if attempt < max_attempts - 1:
                    continue
                break

            board.push(move)
            st.session_state.board = board
            st.session_state.turn = "user"

            captured_piece = board.piece_at(move.to_square)
            captured_unicode = PIECE_UNICODE.get(captured_piece.symbol() if captured_piece else '', '')
            add_log(f"Model responds: {model_move_str} {captured_unicode}", is_user=False)

            if board.is_checkmate():
                st.session_state.status = "ended"
                st.session_state.final_result = {"winner": "model"}
                add_log("😢 AI checkmated your king! AI wins!", is_user=False)
            elif board.is_stalemate():
                st.session_state.status = "ended"
                st.session_state.final_result = {"winner": "draw", "reason": "Stalemate"}
                add_log("🤝 Stalemate!", is_user=False)
            elif board.is_check():
                add_log("⚠️ Check! Your king is under threat!", is_user=False)

            return True

        except requests.exceptions.Timeout:
            error_msg = f"⏱️ Timeout ({FRONTEND_TIMEOUT}s), model is thinking, please try again later"
            st.session_state.debug_info["last_error"] = error_msg
            st.session_state.turn = "user"
            add_log(f"❌ {error_msg}", is_user=False)
            return False
        except requests.exceptions.ConnectionError:
            error_msg = "🔗 Cannot connect to server, please ensure backend service is running"
            st.session_state.debug_info["last_error"] = error_msg
            st.session_state.turn = "user"
            add_log(f"❌ {error_msg}", is_user=False)
            return False
        except requests.exceptions.HTTPError as e:
            error_msg = f"❌ HTTP error: {e.response.status_code}"
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
        f"😵 Model returned invalid moves {max_attempts} times consecutively, game forced to end.",
        is_user=False,
    )
    st.session_state.turn = "user"
    st.session_state.status = "ended"
    st.session_state.final_result = {
        "winner": "draw",
        "reason": "Model returned invalid moves multiple times, game auto-ended",
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
            api_result = data.get("result")
            if isinstance(api_result, dict):
                st.session_state.final_result = api_result
        except:
            pass

        st.session_state.status = "ended"
        add_log("🏁 Game ended", is_user=False)


def handle_square_click(row, col):
    board = st.session_state.board
    sq_name = square_name(row, col)
    piece = board.piece_at(chess.parse_square(sq_name))

    if st.session_state.selected_square is None:
        if piece and piece.color == chess.WHITE:
            st.session_state.selected_square = sq_name
            st.session_state.legal_targets = get_legal_targets_for_square(sq_name)
    else:
        if sq_name == st.session_state.selected_square:
            st.session_state.selected_square = None
            st.session_state.legal_targets = []
        elif piece and piece.color == chess.WHITE:
            st.session_state.selected_square = sq_name
            st.session_state.legal_targets = get_legal_targets_for_square(sq_name)
        elif sq_name in st.session_state.legal_targets:
            from_sq = st.session_state.selected_square
            to_sq = sq_name
            uci_base = from_sq + to_sq

            from_piece = board.piece_at(chess.parse_square(from_sq))
            if from_piece and from_piece.piece_type == chess.PAWN and chess.parse_square(to_sq) >= 56:
                st.session_state.pending_promotion = uci_base
                st.session_state.selected_square = None
                st.session_state.legal_targets = []
                return

            full_uci = uci_base
            try:
                move = chess.Move.from_uci(full_uci)
                if move in board.legal_moves:
                    board.push(move)
                    st.session_state.board = board
                    st.session_state.selected_square = None
                    st.session_state.legal_targets = []
                    add_log(f"You move: {full_uci}", is_user=True)

                    if board.is_checkmate():
                        st.session_state.status = "ended"
                        st.session_state.final_result = {"winner": "user"}
                        add_log("🎉 You checkmated AI's king! You win!", is_user=True)
                    elif board.is_stalemate():
                        st.session_state.status = "ended"
                        st.session_state.final_result = {"winner": "draw", "reason": "Stalemate"}
                        add_log("🤝 Stalemate!", is_user=False)
                    elif board.is_check():
                        add_log("⚠️ Check! AI's king is under threat!", is_user=False)
                        st.session_state.turn = "model"
                        st.session_state.pending_action = full_uci
                    else:
                        st.session_state.turn = "model"
                        st.session_state.pending_action = full_uci
            except (ValueError, chess.AmbiguousMoveError):
                st.session_state.selected_square = None
                st.session_state.legal_targets = []
        else:
            st.session_state.selected_square = None
            st.session_state.legal_targets = []


def inject_board_colors():
    selected_sq = st.session_state.selected_square
    targets = st.session_state.legal_targets

    selected_idx = -1
    if selected_sq:
        sq = chess.parse_square(selected_sq)
        selected_idx = (7 - chess.square_rank(sq)) * 8 + chess.square_file(sq)

    target_indices = []
    for t in targets:
        sq = chess.parse_square(t)
        target_indices.append((7 - chess.square_rank(sq)) * 8 + chess.square_file(sq))

    target_list = ",".join(str(i) for i in target_indices)

    components.html(f"""
    <script>
        (function() {{
            const parent = window.parent.document;
            const buttons = parent.querySelectorAll('div[data-testid="stButton"] button[kind="primary"]');
            const selectedIdx = {selected_idx};
            const targetSet = new Set([{target_list}]);

            buttons.forEach((btn, index) => {{
                if (index >= 64) return;
                const row = Math.floor(index / 8);
                const col = index % 8;
                const isLight = (row + col) % 2 === 0;

                if (index === selectedIdx) {{
                    btn.style.backgroundColor = '#f7dc6f';
                    btn.style.boxShadow = 'inset 0 0 0 3px #e74c3c';
                }} else if (targetSet.has(index)) {{
                    btn.style.backgroundColor = '#82e0aa';
                    btn.style.boxShadow = 'inset 0 0 0 3px #27ae60';
                }} else {{
                    btn.style.backgroundColor = isLight ? '#f0d9b5' : '#b58863';
                    btn.style.boxShadow = 'none';
                }}
            }});
        }})();
    </script>
    """, height=0)


# ================= Game UI =================
if st.session_state.status == "not_started":
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <div style="font-size:72px; margin-bottom:20px;">♟️♔♕♖♗♘</div>
        <p style="color:#a0a0a0; margin-bottom:28px;">Play chess against AI model, you play white, AI plays black</p>
        <p style="color:#a0a0a0; font-size:14px;">Click a piece to select it, then click the target square to move</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Game", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    board = st.session_state.board

    if st.session_state.final_result and st.session_state.final_result.get("winner"):
        winner = st.session_state.final_result["winner"]
        if winner == "user":
            st.success("🎉 You win!")
        elif winner == "model":
            st.error("😢 AI wins!")
    else:
        if board.is_check():
            if board.turn == chess.WHITE:
                st.error("⚠️ Check! Your king is under threat!")
            else:
                st.warning("⚠️ AI's king is in check!")

        current_player = "♔ You (White)" if st.session_state.turn == "user" else "♚ AI (Black)"
        st.info(f"Current turn: {current_player}")

    if st.session_state.pending_promotion:
        st.markdown("---")
        st.subheader("♙ Pawn Promotion")
        st.write(f"Pawn reached the back rank ({st.session_state.pending_promotion}). Please choose a promotion piece:")
        promo_cols = st.columns(4)
        promo_pieces = [("q", "♕ Queen"), ("r", "♖ Rook"), ("b", "♗ Bishop"), ("n", "♘ Knight")]
        for i, (promo_code, promo_label) in enumerate(promo_pieces):
            if promo_cols[i].button(promo_label, key=f"promo_{promo_code}", use_container_width=True):
                full_uci = st.session_state.pending_promotion + promo_code
                st.session_state.pending_promotion = None
                move = chess.Move.from_uci(full_uci)
                board.push(move)
                st.session_state.board = board
                add_log(f"You move: {full_uci} (promotion)", is_user=True)

                if board.is_checkmate():
                    st.session_state.status = "ended"
                    st.session_state.final_result = {"winner": "user"}
                    add_log("🎉 You checkmated AI's king! You win!", is_user=True)
                elif board.is_stalemate():
                    st.session_state.status = "ended"
                    st.session_state.final_result = {"winner": "draw", "reason": "Stalemate"}
                    add_log("🤝 Stalemate!", is_user=False)
                elif board.is_check():
                    add_log("⚠️ Check! AI's king is under threat!", is_user=False)
                    st.session_state.turn = "model"
                    st.session_state.pending_action = full_uci
                else:
                    st.session_state.turn = "model"
                    st.session_state.pending_action = full_uci
                st.rerun()

    inject_board_colors()

    left_spacer, board_area, right_spacer = st.columns([1, 4, 1])
    with board_area:
        for i in range(8):
            cols = st.columns(8)
            for j in range(8):
                sq_name = square_name(i, j)
                piece_symbol = get_piece_at(i, j)

                label = PIECE_UNICODE.get(piece_symbol, "") if piece_symbol else ""

                disabled = (
                    st.session_state.turn != "user"
                    or st.session_state.pending_promotion is not None
                )

                if cols[j].button(
                    label,
                    key=f"sq_{i}_{j}",
                    disabled=disabled,
                    use_container_width=True,
                    type="primary",
                ):
                    handle_square_click(i, j)
                    st.rerun()

    if st.session_state.pending_action is not None and st.session_state.status == "playing":
        action = st.session_state.pending_action
        st.session_state.pending_action = None

        with st.spinner("Model is thinking..."):
            success = make_action(action)
        if success or st.session_state.status == "ended":
            st.rerun()

    st.markdown("---")
    if st.button("End Game", use_container_width=True, key="end_btn"):
        end_game()
        st.rerun()

elif st.session_state.status == "ended":
    final = st.session_state.final_result or {}
    winner = final.get("winner", "")

    if winner == "user":
        st.success("🎉 **You (White)** win!")
    elif winner == "model":
        st.error("😢 AI (Black) wins!")
    elif winner == "draw":
        st.warning("🤝 Draw!")
        if final.get("reason"):
            st.info(final["reason"])
    else:
        st.warning("Game has ended")

    board = st.session_state.board
    st.session_state.selected_square = None
    st.session_state.legal_targets = []
    inject_board_colors()
    left_spacer, board_area, right_spacer = st.columns([1, 4, 1])
    with board_area:
        for i in range(8):
            cols = st.columns(8)
            for j in range(8):
                piece_symbol = get_piece_at(i, j)
                label = PIECE_UNICODE.get(piece_symbol, "") if piece_symbol else ""
                cols[j].button(label, key=f"final_{i}_{j}", disabled=True, use_container_width=True, type="primary")

    if st.session_state.game_summary is not None:
        st.markdown("---")
        st.subheader("📊 Game Summary")
        st.info(st.session_state.game_summary)
    elif st.button("🤖 Generate Game Summary", use_container_width=True):
        with st.spinner("Generating game summary..."):
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
    if st.button("Start Over", use_container_width=True):
        st.session_state.status = "not_started"
        st.session_state.board = chess.Board()
        st.session_state.turn = "user"
        st.session_state.selected_square = None
        st.session_state.legal_targets = []
        st.session_state.game_log = []
        st.session_state.final_result = None
        st.session_state.game_summary = None
        st.session_state.pending_promotion = None
        st.session_state.pending_action = None
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
                    f"<pre style='white-space: pre-wrap; margin: 0; font-size: 13px;'>{log['message']}</pre>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No logs yet")

    if st.session_state.session_id:
        st.divider()
        st.caption(f"Session ID: {st.session_state.session_id}")

    if st.session_state.status == "playing":
        st.divider()
        st.subheader("♟️ Current Board (FEN)")
        fen = st.session_state.board.fen()
        st.code(fen, language="text")
        st.caption(f"Move number: {st.session_state.board.fullmove_number}")
