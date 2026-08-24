"""
主题配置 - 定义明暗两套主题的 CSS 样式
"""


THEMES = {
    "dark": {
        "name": "暗色主题",
        "icon": "🌙",
        "css": """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
            color: #e8e8e8;
        }
        .mp-nav, .mp-nav-bar {
            background: rgba(15, 12, 41, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .mp-nav a, .mp-nav span, .mp-nav-bar a, .mp-nav-bar span { color: #e8e8e8 !important; }
        .mp-nav button, .mp-nav-bar button { color: #e8e8e8 !important; }
        [data-testid="stPageLink"] a, [data-testid="stPageLink"] span { color: #e8e8e8 !important; }
        .mp-section-title { color: #ffffff; }
        .mp-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .mp-card:hover { border-color: #7c3aed; background: rgba(124,58,237,0.15); }
        .mp-footer { background: rgba(0,0,0,0.4); color: #a0a0a0; }
        .mp-about { background: rgba(255,255,255,0.03); }
        .mp-github-btn { background: rgba(255,255,255,0.1); color: #e8e8e8; }
        .mp-github-btn:hover { background: #7c3aed; }
        .mp-theme-btn { background: rgba(255,255,255,0.1); color: #e8e8e8; }
        .mp-theme-btn:hover { background: #f59e0b; }
        [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
    },
    "light": {
        "name": "亮色主题",
        "icon": "☀️",
        "css": """
        <style>
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 50%, #ffffff 100%);
            color: #1a1a2e;
        }
        .mp-nav, .mp-nav-bar {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(0,0,0,0.08);
        }
        .mp-nav a, .mp-nav span, .mp-nav-bar a, .mp-nav-bar span { color: #1a1a2e !important; }
        .mp-nav button, .mp-nav-bar button { color: #1a1a2e !important; }
        [data-testid="stPageLink"] a, [data-testid="stPageLink"] span { color: #1a1a2e !important; }
        .mp-section-title { color: #1a1a2e; }
        .mp-card {
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(0,0,0,0.08);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .mp-card:hover { border-color: #7c3aed; box-shadow: 0 4px 20px rgba(124,58,237,0.2); }
        .mp-footer { background: #1a1a2e; color: #c0c0c0; }
        .mp-about { background: rgba(255,255,255,0.6); }
        .mp-github-btn { background: #1a1a2e; color: #ffffff; }
        .mp-github-btn:hover { background: #7c3aed; }
        .mp-theme-btn { background: rgba(0,0,0,0.08); color: #1a1a2e; }
        .mp-theme-btn:hover { background: #f59e0b; color: #fff; }
        [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
    },
}

GITHUB_URL = "https://github.com"


def get_theme_css(theme: str) -> str:
    """获取指定主题的 CSS"""
    if theme in THEMES:
        return THEMES[theme]["css"]
    return THEMES["dark"]["css"]


def get_theme_info(theme: str) -> dict:
    """获取主题信息"""
    if theme in THEMES:
        return {"name": THEMES[theme]["name"], "icon": THEMES[theme]["icon"]}
    return {"name": THEMES["dark"]["name"], "icon": THEMES["dark"]["icon"]}


def get_opposite_theme(theme: str) -> str:
    """获取相反的主题"""
    return "light" if theme == "dark" else "dark"
