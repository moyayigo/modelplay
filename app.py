import streamlit as st
import sys
import os
import base64
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.theme import get_theme_css, get_theme_info, get_opposite_theme, GITHUB_URL
from src.language import get_text, get_language_info, get_opposite_language
from src.app_config import get_api_base_url

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "language" not in st.session_state:
    st.session_state.language = "en"

LANG = st.session_state.language

st.set_page_config(
    page_title=get_text("app_title", LANG),
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================== 顶部导航栏 ====================
def render_navbar():
    # 根据当前主题动态注入导航栏元素颜色
    is_dark = st.session_state.theme == "dark"
    nav_text = "#e8e8e8" if is_dark else "#1a1a2e"

    st.markdown(f"""
    <style>
    /* GitHub 按钮：文字和图标颜色跟随主题 */
    .mp-github-btn {{ color: {nav_text} !important; }}
    .mp-github-btn svg {{ fill: currentColor !important; }}
    /* 导航栏中的 page_link 文字颜色 */
    [data-testid="stPageLink"] a, [data-testid="stPageLink"] span {{
        color: {nav_text} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col_logo, col_games, col_docs, col_about, col_empty, col_theme, col_lang, col_github = st.columns([2, 2, 1, 1, 8, 1, 1, 1])
    with col_logo:
        st.markdown(
            '<span style="font-size:24px; font-weight:900; letter-spacing:-0.5px;">'
            '<span style="background:linear-gradient(90deg,#7c3aed,#db2777); '
            '-webkit-background-clip:text; -webkit-text-fill-color:transparent;">ModelPlay</span>'
            '</span>',
            unsafe_allow_html=True
        )
    with col_games:
        st.page_link("pages/game_hub.py", label=f"🎮 {get_text('games', LANG)}", use_container_width=True)
    with col_docs:
        st.page_link("pages/modelplay_docs.py", label=f"{get_text('docs', LANG)}", use_container_width=True)
    with col_about:
        st.page_link("pages/modelplay_about.py", label=f"{get_text('about', LANG)}", use_container_width=True)
    with col_empty:
        st.empty()
    with col_theme:
        theme_info = get_theme_info(st.session_state.theme)
        next_theme = get_opposite_theme(st.session_state.theme)
        if st.button(theme_info['icon'], use_container_width=True, key="theme_btn", help=get_text('switch_theme', LANG)):
            st.session_state.theme = next_theme
            st.rerun()
    with col_lang:
        lang_info = get_language_info(st.session_state.language)
        next_lang = get_opposite_language(st.session_state.language)
        if st.button(lang_info['icon'], use_container_width=True, key="lang_btn", help=get_text('switch_language', LANG)):
            st.session_state.language = next_lang
            st.rerun()
    with col_github:
        st.markdown(f"""
        <a href="{GITHUB_URL}" target="_blank" class="mp-github-btn" title="GitHub" style="
            display:inline-block; width:100%; text-align:center; padding:0.5rem 1rem;
            border-radius:0.5rem; text-decoration:none;
        ">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:middle;">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
        </a>
        """, unsafe_allow_html=True)

# ==================== 工具栏按钮（已合并至导航栏） ====================
    


# ==================== 热门游戏 Banner ====================
def render_banner():
    banner_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "assets", "images", "banner_hot.jpeg")
    try:
        with open(banner_path, "rb") as f:
            banner_img = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        banner_img = ""

    banner_html = f"""
    <div id="games" style="
        position: relative; margin: 24px -3rem 0 -3rem; height: 420px;
        background: url('{banner_img}') center/cover no-repeat;
        display: flex; align-items: center;
    ">
        <div style="
            position: absolute; inset: 0;
            background: linear-gradient(90deg, rgba(15,12,41,0.92) 0%, rgba(15,12,41,0.6) 50%, rgba(15,12,41,0.3) 100%);
        "></div>
        <div style="position: relative; z-index: 2; padding: 0 48px; max-width: 640px;">
            <span style="display:inline-block; padding:4px 14px; border-radius:20px;
                         background:rgba(124,58,237,0.3); border:1px solid rgba(124,58,237,0.6);
                         color:#c4b5fd; font-size:13px; font-weight:600; margin-bottom:16px;">
                {get_text('hot_recommend', LANG)}
            </span>
            <h1 style="color:#fff; font-size:48px; font-weight:800; margin:0 0 16px; line-height:1.1;">
                {get_text('game_title', LANG)}
            </h1>
            <p style="color:#cbd5e1; font-size:18px; margin:0 0 28px; line-height:1.6;">
                {get_text('game_desc', LANG)}
            </p>
        </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

    col_btn1, col_spacer = st.columns([3, 4])
    with col_btn1:
        if st.button(get_text('start_now', LANG), type="primary", use_container_width=True, key="start_game_btn"):
            try:
                st.switch_page("pages/Tic_Tac_Toe.py")
            except Exception as e:
                st.error(f"跳转失败: {e}")


# ==================== 项目介绍栏 ====================
def render_about():
    about_html = f"""
    <div class="mp-about" style="
        margin: 48px -3rem 0 -3rem; padding: 60px 48px;
        border-top: 1px solid rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.06);
    ">
        <div style="max-width:960px; margin:0 auto; text-align:center;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
                {get_text('about_title', LANG)}
            </span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 24px;">
                {get_text('about_header', LANG)}
            </h2>
            <p style="font-size:18px; line-height:1.8; opacity:0.85; margin:0 auto; max-width:680px;">
                {get_text('about_desc', LANG)}
            </p>
        </div>
    </div>
    """
    st.markdown(about_html, unsafe_allow_html=True)


# ==================== 特色介绍矩阵 ====================
def render_features():
    features = [
        ("🤖", get_text('feature_1_title', LANG), get_text('feature_1_desc', LANG)),
        ("🎮", get_text('feature_2_title', LANG), get_text('feature_2_desc', LANG)),
        ("📊", get_text('feature_3_title', LANG), get_text('feature_3_desc', LANG)),
        ("⚡", get_text('feature_4_title', LANG), get_text('feature_4_desc', LANG)),
        ("🎨", get_text('feature_5_title', LANG), get_text('feature_5_desc', LANG)),
        ("🔧", get_text('feature_6_title', LANG), get_text('feature_6_desc', LANG)),
    ]

    st.markdown('<div style="margin: 48px -3rem 0 -3rem; padding: 60px 48px;">', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:40px;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">{get_text('features_title', LANG)}</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 0;">{get_text('features_header', LANG)}</h2>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            card_html = f"""
            <div class="mp-card" style="
                padding: 28px; border-radius:16px; margin-bottom:20px;
                transition: all 0.3s ease; height: 200px;
                display:flex; flex-direction:column;
            ">
                <div style="font-size:36px; margin-bottom:16px;">{icon}</div>
                <h3 class="mp-section-title" style="font-size:18px; font-weight:700; margin:0 0 10px;">{title}</h3>
                <p style="font-size:14px; line-height:1.6; opacity:0.75; margin:0;">{desc}</p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 三种应用类型板块 ====================
def render_app_types():
    st.markdown(f"""
    <div style="margin: 48px -3rem 0 -3rem; padding: 60px 48px;">
        <div style="max-width:960px; margin:0 auto;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">{get_text('app_types_title', LANG)}</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 16px;">{get_text('app_types_header', LANG)}</h2>
            <p style="font-size:18px; line-height:1.8; opacity:0.85; margin:0 auto; max-width:680px;">
                {get_text('app_types_desc', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:280px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:20px; margin:0 0 12px;">{get_text('app_type_game_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('app_type_game_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:280px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:20px; margin:0 0 12px;">{get_text('app_type_course_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('app_type_course_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:280px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:20px; margin:0 0 12px;">{get_text('app_type_collab_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('app_type_collab_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)


# ==================== APP 构建器板块 ====================
def render_app_builder():
    st.markdown(f"""
    <div style="margin: 48px -3rem 0 -3rem; padding: 60px 48px; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="max-width:960px; margin:0 auto; text-align:center;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">{get_text('app_builder_title', LANG)}</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 16px;">{get_text('app_builder_header', LANG)}</h2>
            <p style="font-size:18px; line-height:1.8; opacity:0.85; margin:0 auto; max-width:720px;">
                {get_text('app_builder_desc', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("1", get_text('app_builder_step_1', LANG), get_text('app_builder_step_1_desc', LANG)),
        ("2", get_text('app_builder_step_2', LANG), get_text('app_builder_step_2_desc', LANG)),
        ("3", get_text('app_builder_step_3', LANG), get_text('app_builder_step_3_desc', LANG)),
        ("4", get_text('app_builder_step_4', LANG), get_text('app_builder_step_4_desc', LANG)),
    ]
    cols = st.columns(4)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div class="mp-card" style="padding:24px; border-radius:12px; height:200px; display:flex; flex-direction:column;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                    <span style="background:#7c3aed; color:#fff; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:15px; font-weight:700;">{num}</span>
                    <h4 class="mp-section-title" style="margin:0; font-size:15px;">{title}</h4>
                </div>
                <p style="font-size:13px; opacity:0.75; margin:0; line-height:1.6;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)


# ==================== 模型支持板块 ====================
def render_model_support():
    st.markdown(f"""
    <div style="margin: 48px -3rem 0 -3rem; padding: 60px 48px; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="max-width:960px; margin:0 auto;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">{get_text('model_support_title', LANG)}</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 16px;">{get_text('model_support_header', LANG)}</h2>
            <p style="font-size:18px; line-height:1.8; opacity:0.85; margin:0 auto; max-width:680px;">
                {get_text('model_support_desc', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:240px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('model_local_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('model_local_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:240px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('model_cloud_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('model_cloud_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="mp-card" style="padding:28px; border-radius:16px; height:240px; display:flex; flex-direction:column;">
            <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('model_switch_title', LANG)}</h3>
            <p style="font-size:14px; line-height:1.7; opacity:0.8; margin:0;">{get_text('model_switch_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)


# ==================== Token 用量板块 ====================
def render_token_usage():
    """显示今日模型 token 使用量与限额状态。"""
    st.markdown(f"""
    <div style="margin: 48px -3rem 0 -3rem; padding: 60px 48px;">
        <div style="max-width:960px; margin:0 auto;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">Usage</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 32px;">{get_text('token_usage_title', LANG)}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        resp = requests.get(f"{get_api_base_url()}/api/usage", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.warning(f"⚠️ {get_text('token_fetch_failed', LANG)}：{e}")
        return

    used = data.get("used", 0)
    limit = data.get("limit", 0)
    remaining = data.get("remaining", -1)
    call_count = data.get("call_count", 0)
    prompt_tokens = data.get("prompt_tokens", 0)
    completion_tokens = data.get("completion_tokens", 0)
    allowed = data.get("allowed", True)
    reset_at = data.get("reset_at", "")

    # 顶部三列指标
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(get_text('token_used_today', LANG), f"{used:,}")
    with col_b:
        if limit > 0:
            st.metric(get_text('token_remaining', LANG), f"{remaining:,}")
        else:
            st.metric(get_text('token_remaining', LANG), get_text('token_unlimited', LANG))
    with col_c:
        st.metric(get_text('token_call_count', LANG), f"{call_count}")

    # 进度条
    if limit > 0:
        pct = min(100.0, (used / limit) * 100.0) if limit > 0 else 0
        st.write(f"**{get_text('token_progress', LANG)}**: {used:,} / {limit:,} ({pct:.1f}%)")
        st.progress(pct / 100.0)
        if not allowed:
            st.error(f"{get_text('token_limit_reached', LANG)}{reset_at}")
        elif pct >= 80:
            st.warning(f"{get_text('token_warning_80', LANG)}{reset_at}")
    else:
        st.info(get_text('token_no_limit', LANG))

    # 明细
    with st.expander(get_text('token_details', LANG)):
        st.write(f"- {get_text('token_prompt_tokens', LANG)}: **{prompt_tokens:,}**")
        st.write(f"- {get_text('token_completion_tokens', LANG)}: **{completion_tokens:,}**")
        st.write(f"- {get_text('token_stat_date', LANG)}: {data.get('date', '')}")
        st.write(f"- {get_text('token_reset_rule', LANG)}: {reset_at}")


# ==================== 文档区 ====================
def render_docs():
    docs_html = f"""
    <div id="docs" style="
        margin: 0 -3rem 0 -3rem; padding: 60px 48px;
        border-top: 1px solid rgba(255,255,255,0.06);
    ">
        <div style="max-width:960px; margin:0 auto;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">{get_text('docs', LANG)}</span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 32px;">{get_text('quick_start', LANG)}</h2>
        </div>
    </div>
    """
    st.markdown(docs_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mp-card" style="padding:24px; border-radius:12px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <span style="background:#7c3aed; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700;">1</span>
                <h4 class="mp-section-title" style="margin:0; font-size:16px;">{get_text('step_1_title', LANG)}</h4>
            </div>
            <pre style="background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; font-size:13px; margin:0; overflow-x:auto;"><code>python src/api_server.py</code></pre>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="mp-card" style="padding:24px; border-radius:12px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <span style="background:#7c3aed; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700;">2</span>
                <h4 class="mp-section-title" style="margin:0; font-size:16px;">{get_text('step_2_title', LANG)}</h4>
            </div>
            <pre style="background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; font-size:13px; margin:0; overflow-x:auto;"><code>streamlit run index.py</code></pre>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="mp-card" style="padding:24px; border-radius:12px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <span style="background:#7c3aed; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700;">3</span>
                <h4 class="mp-section-title" style="margin:0; font-size:16px;">{get_text('step_3_title', LANG)}</h4>
            </div>
            <p style="font-size:14px; opacity:0.75; margin:0; line-height:1.6;">{get_text('step_3_desc', LANG)}</p>
        </div>
        """, unsafe_allow_html=True)


# ==================== Footer ====================
def render_footer():
    footer_html = f"""
    <div class="mp-footer" style="
        margin: 60px -3rem -3rem -3rem; padding: 40px 48px 24px;
    ">
        <div style="max-width:1200px; margin:0 auto; display:flex; flex-wrap:wrap; justify-content:space-between; gap:32px;">
            <div style="flex:1; min-width:200px;">
                <div style="font-size:20px; font-weight:800; margin-bottom:12px;">
                    🎮 <span style="background:linear-gradient(90deg,#7c3aed,#db2777); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">ModelPlay</span>
                </div>
                <p style="font-size:13px; line-height:1.6; margin:0; opacity:0.7;">
                    {get_text('footer_desc', LANG)}
                </p>
            </div>
            <div>
                <h5 style="font-size:14px; font-weight:600; margin:0 0 12px;">{get_text('tech_stack', LANG)}</h5>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <span style="font-size:13px; opacity:0.8;">⚡ Streamlit + FastAPI</span>
                    <span style="font-size:13px; opacity:0.8;">🤖 Ollama / llama.cpp</span>
                    <span style="font-size:13px; opacity:0.8;">🐍 Python 3.10+</span>
                </div>
            </div>
        </div>
        <div style="border-top:1px solid rgba(255,255,255,0.1); margin-top:32px; padding-top:20px; text-align:center;">
            <p style="font-size:12px; opacity:0.6; margin:0;">
                {get_text('copyright', LANG)}
            </p>
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


# ==================== 渲染页面 ====================
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

render_navbar()
render_banner()
render_about()
render_features()
render_app_types()
render_app_builder()
render_model_support()
render_token_usage()
render_docs()
render_footer()
