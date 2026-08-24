import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import requests

from src.theme import get_theme_css, get_theme_info, get_opposite_theme, GITHUB_URL
from src.language import get_text, get_language_info, get_opposite_language
from src.app_config import get_api_base_url

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "language" not in st.session_state:
    st.session_state.language = "zh"

LANG = st.session_state.language

st.set_page_config(
    page_title=get_text("game_hub_title", LANG),
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def cleanup_previous_game():
    """检测并关闭之前未结束的游戏会话，清理跨游戏残留状态。

    各游戏共享 st.session_state 中的 session_id/status 等键，若上一局游戏
    未正常结束就返回大厅并启动新游戏，残留状态会污染新游戏导致报错。
    此函数在大厅加载时自动结束后端会话并清空游戏相关状态（保留主题/语言）。
    返回 True 表示执行了清理。
    """
    session_id = st.session_state.get("session_id")
    status = st.session_state.get("status")

    # 判断是否存在残留的游戏会话（已启动但未清理）
    has_leftover = session_id is not None or status not in (None, "not_started")
    if not has_leftover:
        return False

    # 会话仍在进行中时，调用后端接口结束会话，释放资源
    if session_id and status == "playing":
        try:
            requests.post(
                f"{get_api_base_url()}/api/game/end/{session_id}",
                timeout=10,
            )
        except requests.exceptions.RequestException:
            pass  # 后端不可用时静默忽略，仅清理前端状态

    # 清除所有游戏相关状态，仅保留主题与语言设置，确保新游戏从干净状态启动
    preserve = {"theme", "language"}
    for key in list(st.session_state.keys()):
        if key not in preserve:
            del st.session_state[key]

    return True


def render_toolbar():
    col1, col2, col3, col4 = st.columns([20, 1, 1, 1])
    with col1:
        st.empty()
    with col2:
        theme_info = get_theme_info(st.session_state.theme)
        next_theme = get_opposite_theme(st.session_state.theme)
        if st.button(theme_info['icon'], use_container_width=True, key="theme_btn", help=get_text('switch_theme', LANG)):
            st.session_state.theme = next_theme
            st.rerun()
    with col3:
        lang_info = get_language_info(st.session_state.language)
        next_lang = get_opposite_language(st.session_state.language)
        if st.button(lang_info['icon'], use_container_width=True, key="lang_btn", help=get_text('switch_language', LANG)):
            st.session_state.language = next_lang
            st.rerun()
    with col4:
        st.markdown(f"""
        <a href="{GITHUB_URL}" target="_blank" title="GitHub" style="
            display:inline-block; width:100%; text-align:center; padding:0.5rem 1rem;
            border-radius:0.5rem; text-decoration:none;
        ">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:middle;">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
        </a>
        """, unsafe_allow_html=True)


def scan_games():
    pages_dir = os.path.dirname(os.path.abspath(__file__))
    games = []

    ignore_files = {"game_hub.py", "modelplay_docs.py", "modelplay_about.py"}

    for filename in os.listdir(pages_dir):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
        if filename in ignore_files:
            continue
        filepath = os.path.join(pages_dir, filename)
        game_info = parse_game_file(filepath, filename)
        if game_info:
            games.append(game_info)

    games.sort(key=lambda x: x["order"])
    return games


def parse_game_file(filepath, filename):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        order = 999
        order_match = re.match(r'(\d+)_', filename)
        if order_match:
            order = int(order_match.group(1))

        display_name = re.sub(r'^\d+_', '', filename).replace('.py', '').replace('_', ' ').title()

        page_title = None
        title_match = re.search(r'page_title\s*=\s*["\']([^"\']+)["\']', content)
        if title_match:
            page_title = title_match.group(1)

        page_icon = "🎮"
        icon_match = re.search(r'page_icon\s*=\s*["\']([^"\']+)["\']', content)
        if icon_match:
            page_icon = icon_match.group(1)

        game_meta = {}
        meta_match = re.search(r'GAME_META\s*=\s*\{([^}]+)\}', content, re.DOTALL)
        if meta_match:
            try:
                meta_content = meta_match.group(1)
                title_match2 = re.search(r'"title"\s*:\s*"([^"]*)"', meta_content)
                if title_match2:
                    page_title = title_match2.group(1)
                icon_match2 = re.search(r'"icon"\s*:\s*"([^"]*)"', meta_content)
                if icon_match2:
                    page_icon = icon_match2.group(1)
                desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', meta_content)
                if desc_match:
                    display_name = desc_match.group(1)
            except:
                pass

        return {
            "filename": filename,
            "filepath": f"pages/{filename}",
            "name": page_title or display_name,
            "icon": page_icon,
            "description": display_name,
            "order": order,
        }
    except Exception as e:
        return None


def render_game_cards(games):
    if not games:
        st.warning(get_text("no_games_found", LANG))
        return

    cols_per_row = 3
    for i in range(0, len(games), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(games):
                game = games[idx]
                with cols[j]:
                    card_html = f"""
                    <div class="mp-card" style="margin-bottom: 20px;">
                        <div style="font-size:48px; margin-bottom:16px; text-align:center;">{game['icon']}</div>
                        <h3 class="mp-section-title" style="font-size:20px; font-weight:700; margin:0 0 8px; text-align:center;">{game['name']}</h3>
                        <p style="font-size:14px; line-height:1.5; opacity:0.7; margin:0; text-align:center; min-height:42px;">{game['description']}</p>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    if st.button(f"▶ {get_text('play', LANG)}", key=f"play_{idx}", use_container_width=True, type="primary"):
                        try:
                            st.switch_page(game["filepath"])
                        except Exception as e:
                            st.error(f"{get_text('open_game_fail', LANG)}: {e}")


def main():
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    if cleanup_previous_game():
        st.toast(get_text("cleanup_game_notice", LANG))

    render_toolbar()

    st.title(f"🎮 {get_text('game_hub_title', LANG)}")
    st.markdown(get_text("game_hub_desc", LANG))

    st.markdown("---")

    games = scan_games()

    if games:
        st.subheader(f"{get_text('available_games', LANG)} ({len(games)})")
        render_game_cards(games)
    else:
        st.info(get_text("no_games_info", LANG))

    st.markdown("---")

    st.subheader(get_text("how_to_add_game", LANG))
    st.markdown(f"""
    1. Create a new `.py` file in the `pages/` directory (e.g., `2_tic_tac_toe.py`)
    2. Add game metadata at the top of the file:
    ```python
    GAME_META = {{
        "title": "Tic Tac Toe",
        "icon": "⭕",
        "description": "Classic tic-tac-toe game against AI",
    }}
    ```
    3. Implement the game logic using the ModelPlay API
    4. {get_text('game_auto_appear', LANG)}
    """)

    st.markdown("---")
    st.caption(get_text("game_hub_footer", LANG))


if __name__ == "__main__":
    main()
