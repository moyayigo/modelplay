import sys
import os
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from src.theme import get_theme_css, get_theme_info, get_opposite_theme, GITHUB_URL
from src.language import get_text, get_language_info, get_opposite_language

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "language" not in st.session_state:
    st.session_state.language = "en"

LANG = st.session_state.language

st.set_page_config(
    page_title=get_text("about_page_title", LANG),
    page_icon="ℹ️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


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


def load_qr_image():
    qr_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "assets", "images", "qr-discord.png"
    )
    try:
        with open(qr_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        return None


def render_hero():
    st.markdown(f"""
    <div style="
        position: relative; margin: 24px -3rem 0 -3rem; height: 320px;
        background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(219,39,119,0.1) 100%);
        display: flex; align-items: center; justify-content: center;
        border-radius: 0 0 24px 24px;
    ">
        <div style="text-align:center; padding: 0 48px;">
            <div style="font-size:64px; margin-bottom:16px;">🎮</div>
            <h1 class="mp-section-title" style="font-size:48px; font-weight:800; margin:0 0 16px; line-height:1.1;">
                {get_text('about_page_title', LANG)}
            </h1>
            <p style="font-size:20px; opacity:0.8; margin:0;">
                {get_text('about_page_subtitle', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_project_overview():
    st.markdown(f"""
    <div style="max-width:960px; margin:48px auto 0 auto; text-align:center;">
        <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
            {get_text('about_project_title', LANG)}
        </span>
        <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 24px;">
            ModelPlay
        </h2>
        <p style="font-size:18px; line-height:1.8; opacity:0.85; margin:0 auto; max-width:720px;">
            {get_text('about_project_desc', LANG)}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_highlights():
    highlights = [
        ("🖥️", get_text('about_feature_1', LANG)),
        ("🔌", get_text('about_feature_2', LANG)),
        ("🎯", get_text('about_feature_3', LANG)),
        ("🔍", get_text('about_feature_4', LANG)),
    ]

    st.markdown(f"""
    <div style="max-width:960px; margin:48px auto 0 auto;">
        <div style="text-align:center; margin-bottom:32px;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
                {get_text('about_features_title', LANG)}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for i, (icon, desc) in enumerate(highlights):
        with cols[i]:
            card_html = f"""
            <div class="mp-card" style="
                padding: 28px 20px; border-radius:16px; text-align:center;
                transition: all 0.3s ease; min-height: 180px;
            ">
                <div style="font-size:40px; margin-bottom:16px;">{icon}</div>
                <p style="font-size:14px; line-height:1.6; opacity:0.8; margin:0;">{desc}</p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def render_contact():
    st.markdown(f"""
    <div style="max-width:960px; margin:64px auto 0 auto;">
        <div style="text-align:center; margin-bottom:32px;">
            <span style="color:#7c3aed; font-size:14px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
                {get_text('about_contact_title', LANG)}
            </span>
            <h2 class="mp-section-title" style="font-size:36px; font-weight:800; margin:12px 0 16px;">
                {get_text('about_contact_title', LANG)}
            </h2>
            <p style="font-size:16px; opacity:0.8; margin:0;">
                {get_text('about_contact_desc', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_email, col_discord = st.columns(2)

    with col_email:
        st.markdown(f"""
        <div class="mp-card" style="padding:32px; border-radius:16px; text-align:center;">
            <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('about_email_label', LANG)}</h3>
            <div style="
                display:inline-block; padding:10px 20px; border-radius:8px;
                background:rgba(124,58,237,0.15); color:#7c3aed;
                font-size:16px; font-weight:600; letter-spacing:0.5px;
            ">
                yyt20130805@gmail.com
            </div>
            <p style="height:110px; line-height:12px; opacity:0.6; margin-top:12px;"></p>
        </div>
        """, unsafe_allow_html=True)

    with col_discord:
        qr_b64 = load_qr_image()
        if qr_b64:
            st.markdown(f"""
            <div class="mp-card" style="padding:32px; border-radius:16px; text-align:center;">
                <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('about_discord_label', LANG)}</h3>
                <img src="data:image/png;base64,{qr_b64}" style="
                    width: 120px; height: 120px; border-radius:12px;
                    display:inline-block; margin: 8px auto;
                ">
                <p style="font-size:12px; opacity:0.6; margin-top:12px;">
                    {get_text('about_discord_desc', LANG)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="mp-card" style="padding:32px; border-radius:16px; text-align:center;">
                <div style="font-size:48px; margin-bottom:16px;">💬</div>
                <h3 class="mp-section-title" style="font-size:18px; margin:0 0 12px;">{get_text('about_discord_label', LANG)}</h3>
                <p style="font-size:14px; opacity:0.6; margin:20px 0;">
                    {get_text('about_discord_desc', LANG)}
                </p>
            </div>
            """, unsafe_allow_html=True)


def render_footer():
    st.markdown(f"""
    <div style="max-width:960px; margin:64px auto 0 auto; text-align:center;">
        <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:32px;">
            <div style="font-size:24px; font-weight:800; margin-bottom:12px;">
                🎮 <span style="background:linear-gradient(90deg,#7c3aed,#db2777); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">ModelPlay</span>
            </div>
            <p style="font-size:13px; opacity:0.6; margin:0;">
                {get_text('about_version', LANG)}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    render_toolbar()
    render_hero()
    render_project_overview()
    render_highlights()
    render_contact()
    render_footer()


if __name__ == "__main__":
    main()