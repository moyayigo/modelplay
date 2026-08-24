"""
多语言配置 - 中英文 i18n 对照文本
"""


LANGUAGES = {
    "en": {
        "name": "English",
        "icon": "中",
    },
    "zh": {
        "name": "中文",
        "icon": "EN",
    },
}

UI_TEXTS = {
    # 通用
    "app_title": {"zh": "ModelPlay - AI 游戏平台", "en": "ModelPlay - AI Gaming Platform"},
    "home": {"zh": "首页", "en": "Home"},
    "games": {"zh": "游戏中心", "en": "Games Hub"},
    "docs": {"zh": "文档", "en": "Docs"},
    "about": {"zh": "关于", "en": "About"},
    "github": {"zh": "GitHub", "en": "GitHub"},
    "switch_theme": {"zh": "切换主题", "en": "Switch Theme"},
    "switch_language": {"zh": "Switch Language", "en": "切换语言"},

    # 主页 Banner
    "hot_recommend": {"zh": "🔥 热门推荐", "en": "🔥 Hot Recommended"},
    "game_title": {"zh": "井字棋对战", "en": "Tic-Tac-Toe Battle"},
    "game_desc": {
        "zh": "与 AI 模型在 3×3 棋盘上轮流落子，连成三子即胜。<br>考验你的策略与布局，一键开启你的 AI 对战之旅。",
        "en": "Take turns placing marks on a 3×3 grid with the AI, first to connect three in a line wins.<br>Test your strategy and tactics, start your AI battle journey with one click.",
    },
    "start_now": {"zh": "▶ 立即开始游戏", "en": "▶ Start Now"},
    "view_docs": {"zh": "📖 查看文档", "en": "📖 View Docs"},

    # 关于
    "about_title": {"zh": "关于项目", "en": "About"},
    "about_header": {"zh": "让 AI 成为你的游戏对手", "en": "Let AI Be Your Game Opponent"},
    "about_desc": {
        "zh": "ModelPlay 是一个基于本地大语言模型的游戏对战平台。通过通用的后端 API 与灵活的前端框架，你可以快速接入任意类型的游戏 —— 数字填空、文字冒险、策略对战，只需定义游戏规则，其余交给 AI。平台支持自定义 Prompt、实时对话日志、模型原始回复调试，让每一次对战都透明可控。",
        "en": "ModelPlay is a game battle platform based on local large language models. Through a universal backend API and flexible frontend framework, you can quickly integrate any type of game - number filling, text adventure, strategy battle. Just define the game rules, let AI handle the rest. The platform supports custom prompts, real-time chat logs, and raw model response debugging, making every battle transparent and controllable.",
    },

    # 特色
    "features_title": {"zh": "核心特色", "en": "Core Features"},
    "features_header": {"zh": "为什么选择 ModelPlay", "en": "Why Choose ModelPlay"},
    "feature_1_title": {"zh": "本地模型推理", "en": "Local Model Inference"},
    "feature_1_desc": {"zh": "支持 Ollama / llama.cpp 等本地推理后端，数据不出本机，隐私安全有保障", "en": "Supports local inference backends like Ollama / llama.cpp, data stays on your machine, privacy guaranteed"},
    "feature_2_title": {"zh": "通用游戏框架", "en": "Universal Game Framework"},
    "feature_2_desc": {"zh": "前后端完全解耦，只需定义游戏规则 Prompt，即可接入新游戏类型", "en": "Frontend and backend are fully decoupled, just define the game rule prompt to integrate new game types"},
    "feature_3_title": {"zh": "透明对话日志", "en": "Transparent Chat Logs"},
    "feature_3_desc": {"zh": "完整记录系统提示词、用户消息、模型原始回复，便于调试与优化", "en": "Complete recording of system prompts, user messages, and raw model responses for debugging and optimization"},
    "feature_4_title": {"zh": "实时状态管理", "en": "Real-time State Management"},
    "feature_4_desc": {"zh": "基于 FastAPI 的会话管理，支持多游戏实例并行运行", "en": "Session management based on FastAPI, supports parallel execution of multiple game instances"},
    "feature_5_title": {"zh": "明暗主题切换", "en": "Dark/Light Theme Switch"},
    "feature_5_desc": {"zh": "精致的 UI 设计，支持明暗双主题，适配不同使用场景", "en": "Exquisite UI design, supports dark and light themes, adaptable to different usage scenarios"},
    "feature_6_title": {"zh": "灵活可扩展", "en": "Flexible and Extensible"},
    "feature_6_desc": {"zh": "模块化架构，Prompt 管理器、LLM 接口均可独立替换与扩展", "en": "Modular architecture, Prompt manager and LLM interfaces can be independently replaced and extended"},

    # 快速上手
    "quick_start": {"zh": "快速上手", "en": "Quick Start"},
    # Token 用量
    "token_usage_title": {"zh": "今日模型用量", "en": "Today's Model Usage"},
    "token_used_today": {"zh": "📊 今日已用 Token", "en": "📊 Used Today"},
    "token_remaining": {"zh": "✅ 剩余额度", "en": "✅ Remaining"},
    "token_unlimited": {"zh": "无限制", "en": "Unlimited"},
    "token_call_count": {"zh": "🔄 调用次数", "en": "🔄 Call Count"},
    "token_progress": {"zh": "使用进度", "en": "Usage Progress"},
    "token_limit_reached": {
        "zh": "🚫 今日 token 用量已达限额，模型调用已被暂停。重置时间：",
        "en": "🚫 Today's token usage has reached the limit. Model calls are suspended. Reset at: ",
    },
    "token_warning_80": {
        "zh": "⚠️ 今日用量已超过 80%，请留意剩余额度。重置时间：",
        "en": "⚠️ Today's usage has exceeded 80%. Please mind the remaining quota. Reset at: ",
    },
    "token_no_limit": {"zh": "当前未设置每日限额（daily_token_limit = 0）", "en": "No daily limit set (daily_token_limit = 0)"},
    "token_details": {"zh": "明细", "en": "Details"},
    "token_prompt_tokens": {"zh": "输入 Token (prompt)", "en": "Input Tokens (prompt)"},
    "token_completion_tokens": {"zh": "输出 Token (completion)", "en": "Output Tokens (completion)"},
    "token_stat_date": {"zh": "统计日期", "en": "Stat Date"},
    "token_reset_rule": {"zh": "重置规则", "en": "Reset Rule"},
    "token_fetch_failed": {"zh": "无法获取用量数据（后端可能未启动）", "en": "Cannot fetch usage data (backend may not be running)"},
    "step_1_title": {"zh": "启动后端服务", "en": "Start Backend Service"},
    "step_2_title": {"zh": "启动游戏平台", "en": "Start Gaming Platform"},
    "step_3_title": {"zh": "开始对战", "en": "Start Battle"},
    "step_3_desc": {"zh": "点击「开始游戏」，输入数字，AI 将做出回应。在对话日志中查看完整交互过程。", "en": "Click 'Start Game', input a number, and the AI will respond. View the complete interaction in the chat log."},

    # 三种应用类型
    "app_types_title": {"zh": "三种应用类型", "en": "Three Application Types"},
    "app_types_header": {"zh": "不止于游戏，更是一个 AI 交互框架", "en": "More Than Games, an AI Interaction Framework"},
    "app_types_desc": {
        "zh": "ModelPlay 支持三种典型 AI 交互模式，覆盖娱乐、教育、协作三大场景",
        "en": "ModelPlay supports three typical AI interaction patterns, covering entertainment, education, and collaboration",
    },
    "app_type_game_title": {"zh": "🎮 对战游戏", "en": "🎮 Battle Games"},
    "app_type_game_desc": {
        "zh": "用户与 AI 轮流对抗，前端负责判定胜负、管理比分。典型应用：井字棋、石头剪刀布、猜数字、国际象棋",
        "en": "User and AI take turns competing. Frontend handles win/loss judgment and score. Examples: Tic-Tac-Toe, Rock-Paper-Scissors, Number Guessing, Chess",
    },
    "app_type_course_title": {"zh": "📚 互动课程", "en": "📚 Interactive Courses"},
    "app_type_course_desc": {
        "zh": "AI 作为引导者主动提问，学生回答后获得评估反馈。预设轮数完成后生成学习报告。典型应用：英语口语辅导",
        "en": "AI acts as a guide, proactively asking questions. Students answer and receive feedback. A learning report is generated after preset rounds. Example: English Speaking Tutor",
    },
    "app_type_collab_title": {"zh": "🤝 人机协同", "en": "🤝 Human-AI Collaboration"},
    "app_type_collab_desc": {
        "zh": "用户与 AI 共建产物，用户可对 AI 建议做出接受/拒绝/修改反馈，AI 据此调整后续建议。典型应用：旅行规划师",
        "en": "User and AI co-create deliverables. User can accept/reject/edit AI suggestions, and AI adjusts accordingly. Example: Travel Planner",
    },

    # APP 构建器
    "app_builder_title": {"zh": "AI 应用构建器", "en": "AI App Builder"},
    "app_builder_header": {"zh": "用自然语言描述需求，AI 帮你生成应用", "en": "Describe Your Needs in Natural Language, AI Builds the App"},
    "app_builder_desc": {
        "zh": "无需手写代码，只需用自然语言描述你想要的应用（游戏、课程或协同工具），AI 会自动完成需求分析、方案设计、代码生成，并将生成的应用保存到 pages 目录，立即可以在游戏中心运行。",
        "en": "No coding required. Just describe the app you want (game, course, or collaboration tool) in natural language. AI handles requirement analysis, design, and code generation, saving the app to the pages directory, ready to run immediately.",
    },
    "app_builder_step_1": {"zh": "📝 描述需求", "en": "📝 Describe Requirements"},
    "app_builder_step_1_desc": {"zh": "用自然语言描述你想要的应用", "en": "Describe the app you want in natural language"},
    "app_builder_step_2": {"zh": "📐 方案设计", "en": "📐 Design"},
    "app_builder_step_2_desc": {"zh": "AI 分析需求并设计应用方案", "en": "AI analyzes requirements and designs the app"},
    "app_builder_step_3": {"zh": "💻 代码生成", "en": "💻 Code Generation"},
    "app_builder_step_3_desc": {"zh": "基于开发模板生成完整可运行的代码", "en": "Generates complete runnable code based on the template"},
    "app_builder_step_4": {"zh": "🚀 一键运行", "en": "🚀 One-Click Run"},
    "app_builder_step_4_desc": {"zh": "保存到 pages 目录，立即在游戏中心启动", "en": "Saved to pages directory, ready to run in the Games Hub"},

    # 模型支持
    "model_support_title": {"zh": "模型支持", "en": "Model Support"},
    "model_support_header": {"zh": "本地优先，云端兼容", "en": "Local First, Cloud Compatible"},
    "model_support_desc": {
        "zh": "ModelPlay 采用 OpenAI 兼容 API，同时支持本地推理与云端模型，通过配置文件灵活切换",
        "en": "ModelPlay uses OpenAI-compatible API, supporting both local inference and cloud models, switchable via config file",
    },
    "model_local_title": {"zh": "🖥️ 本地模型", "en": "🖥️ Local Models"},
    "model_local_desc": {
        "zh": "支持 Ollama / llama.cpp 等本地推理后端，数据不出本机，隐私安全有保障。适合离线场景与敏感数据处理",
        "en": "Supports local inference backends like Ollama / llama.cpp. Data stays on your machine. Suitable for offline scenarios and sensitive data",
    },
    "model_cloud_title": {"zh": "☁️ 云端模型", "en": "☁️ Cloud Models"},
    "model_cloud_desc": {
        "zh": "兼容 OpenAI、通义、agnes 等 OpenAI 兼容 API 的云端服务。填入 API Key 即可启用，适合需要大模型能力的场景",
        "en": "Compatible with OpenAI-compatible cloud services like OpenAI, Qwen, agnes. Just enter your API Key. Suitable for scenarios requiring large model capabilities",
    },
    "model_switch_title": {"zh": "🔄 灵活切换", "en": "🔄 Flexible Switching"},
    "model_switch_desc": {
        "zh": "通过 config/models.json 配置文件管理多个模型供应商，支持 API 热切换，无需重启服务",
        "en": "Manage multiple model providers via config/models.json. Supports hot-switching via API without service restart",
    },

    # Footer
    "footer_desc": {
        "zh": "基于本地大语言模型的 AI 游戏对战平台<br>让每一次游戏都成为 AI 探索的旅程",
        "en": "AI game battle platform based on local LLMs<br>Making every game a journey of AI exploration",
    },
    "resources": {"zh": "资源", "en": "Resources"},
    "tech_stack": {"zh": "技术栈", "en": "Tech Stack"},
    "copyright": {"zh": "© 2026 ModelPlay · Built with Streamlit · Powered by Local LLM", "en": "© 2026 ModelPlay · Built with Streamlit · Powered by Local LLM"},
    "back_to_top": {"zh": "↑ 返回顶部", "en": "↑ Back to Top"},

    # 调试面板（共享）
    "check_connection": {"zh": "检查连接", "en": "Check Connection"},
    "view_docs": {"zh": "查看文档", "en": "View Docs"},
    "connection_ok": {"zh": "✅ 服务器在线", "en": "✅ Server Online"},
    "connection_fail": {"zh": "❌ 无法连接", "en": "❌ Cannot Connect"},

    # Game Hub
    "game_hub_title": {"zh": "游戏大厅", "en": "Game Hub"},
    "game_hub_desc": {"zh": "浏览并选择一个游戏与 AI 对战", "en": "Browse and select a game to play against the AI"},
    "no_games_found": {"zh": "未找到游戏。请在 pages/ 目录下添加 .py 文件。", "en": "No games found. Add .py files to the pages/ directory."},
    "play": {"zh": "开始", "en": "Play"},
    "open_game_fail": {"zh": "打开游戏失败", "en": "Failed to open game"},
    "available_games": {"zh": "可用游戏", "en": "Available Games"},
    "no_games_info": {"zh": "🎯 暂无游戏。请将游戏文件添加到 pages/ 目录。", "en": "🎯 No games found yet. Add game files to the pages/ directory."},
    "how_to_add_game": {"zh": "📖 如何添加新游戏", "en": "📖 How to Add a New Game"},
    "game_auto_appear": {"zh": "游戏将自动在此页面显示", "en": "The game will automatically appear on this page"},
    "game_hub_footer": {"zh": "ModelPlay 游戏大厅 · 本地大模型驱动", "en": "ModelPlay Game Hub · Powered by Local LLM"},
    "cleanup_game_notice": {"zh": "已自动关闭上一次未结束的游戏会话", "en": "Auto-closed the previous unfinished game session"},

    # About page
    "about_page_title": {"zh": "关于 ModelPlay", "en": "About ModelPlay"},
    "about_page_subtitle": {"zh": "让 AI 成为你的游戏对手", "en": "Let AI Be Your Game Opponent"},
    "about_project_title": {"zh": "项目简介", "en": "Project Overview"},
    "about_project_desc": {
        "zh": "ModelPlay 是一个基于本地大语言模型的 AI 游戏对战与交互框架。通过通用的后端 API 与灵活的前端模板，你可以快速接入任意类型的 AI 交互应用 —— 对战游戏、互动课程、人机协同工具，只需定义规则，其余交给 AI。",
        "en": "ModelPlay is an AI game battle and interaction framework based on local large language models. Through a universal backend API and flexible frontend template, you can quickly integrate any type of AI interaction app — battle games, interactive courses, human-AI collaboration tools. Just define the rules, let AI handle the rest.",
    },
    "about_features_title": {"zh": "核心亮点", "en": "Key Highlights"},
    "about_feature_1": {"zh": "本地模型推理，数据不出本机，隐私安全有保障", "en": "Local model inference, data stays on your machine, privacy guaranteed"},
    "about_feature_2": {"zh": "前后端解耦，只需定义 Prompt 即可接入新应用", "en": "Frontend and backend decoupled, integrate new apps by defining prompts"},
    "about_feature_3": {"zh": "支持对战游戏、互动课程、人机协同三种应用类型", "en": "Supports battle games, interactive courses, and human-AI collaboration"},
    "about_feature_4": {"zh": "实时对话日志与模型原始回复调试，透明可控", "en": "Real-time chat logs and raw model response debugging, transparent and controllable"},
    "about_contact_title": {"zh": "联系方式", "en": "Contact"},
    "about_contact_desc": {
        "zh": "如有任何问题、建议或合作意向，欢迎通过以下方式联系我们：",
        "en": "For any questions, suggestions, or collaboration inquiries, feel free to contact us:",
    },
    "about_email_label": {"zh": "📧 邮箱", "en": "📧 Email"},
    "about_discord_label": {"zh": "💬 Discord 频道", "en": "💬 Discord Channel"},
    "about_discord_desc": {
        "zh": "扫描下方二维码加入 ModelPlay Discord 频道，与社区成员交流讨论",
        "en": "Scan the QR code below to join the ModelPlay Discord channel and chat with the community",
    },
    "about_tech_title": {"zh": "技术栈", "en": "Tech Stack"},
    "about_version": {"zh": "版本 v1.0 · Built with Streamlit & FastAPI", "en": "Version v1.0 · Built with Streamlit & FastAPI"},
}


def get_text(key: str, language: str = "zh") -> str:
    """获取指定语言的文本"""
    if key in UI_TEXTS:
        if language in UI_TEXTS[key]:
            return UI_TEXTS[key][language]
        return UI_TEXTS[key].get("zh", key)
    return key


def get_language_info(lang: str) -> dict:
    """获取语言信息"""
    if lang in LANGUAGES:
        return LANGUAGES[lang]
    return LANGUAGES["zh"]


def get_opposite_language(lang: str) -> str:
    """获取相反的语言"""
    return "en" if lang == "zh" else "zh"
