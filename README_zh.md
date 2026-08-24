# 🎮 ModelPlay

> 基于 LLM 的 AI 交互平台 —— 让 AI 成为你游戏对手、学习导师、协同伙伴

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 项目简介

**ModelPlay** 是一个基于本地大语言模型（LLM）的 AI 交互平台。它将 AI 交互抽象为三种典型模式：**对战游戏**、**互动课程**、**人机协同**，并提供通用的前后端框架，让你可以快速接入任意 AI 交互场景。

平台内置 **AI 应用构建器**，只需用自然语言描述需求，即可自动生成符合平台架构的完整应用。

### ✨ 核心特色

- 🖥️ **本地优先**：支持 Ollama / llama.cpp 等本地推理后端，数据不出本机
- ☁️ **云端兼容**：兼容 OpenAI 等 OpenAI 兼容 API 的云端服务，填入 API Key 即可启用
- 🎮 **通用框架**：前后端完全解耦，只需定义 Prompt 即可接入新应用
- 🤖 **AI 构建器**：用自然语言描述需求，AI 自动生成应用代码
- 📊 **用量追踪**：每日 Token 计数与限额管理，可视化展示用量
- 🌗 **明暗主题**：精致 UI，支持明暗双主题与中英文双语
- 🔧 **模块化**：Prompt 管理、LLM 接口均可独立替换与扩展

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 本地模型推理后端（Ollama / llama.cpp）或云端 API Key

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/modelplay.git
cd modelplay

# 2. 安装依赖
pip install streamlit fastapi uvicorn requests pydantic

# 3. 配置模型（编辑 config/models.json）
{
    "active_provider": "local_ollama",
    "providers": {
        "local_ollama": {
            "name": "Ollama 本地",
            "model": "qwen2.5:7b",
            "api_url": "http://localhost:11434/v1",
            "api_key": "",
            "max_tokens": 4096,
            "timeout": 420
        }
    }
}

# 4. 启动后端服务
python src/api_server.py

# 5. 启动前端平台（新开终端）
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501` 即可开始使用。

## 🏗️ 三种应用类型

ModelPlay 支持三种典型 AI 交互模式：

### 🎮 对战游戏 (Game)

用户与 AI 轮流对抗，前端负责判定胜负、管理比分。

**典型应用：**
- 井字棋 (Tic-Tac-Toe)
- 石头剪刀布 (Rock-Paper-Scissors)
- 猜数字 (Number Guessing)
- 国际象棋 (Chess)

**设计原则：**
- 模型只负责"出招"（返回动作）
- 胜负判定、比分管理、胜利条件检查全部在前端实现
- 不要让模型自导自演

### 📚 互动课程 (Course)

AI 作为引导者主动提问，学生回答后获得评估反馈。

**典型应用：**
- 英语口语辅导 (English Tutor)

**设计原则：**
- AI 主动提问，引导学习
- 学生回答后给出即时反馈
- 预设轮数完成后生成学习报告

### 🤝 人机协同 (Collaborative)

用户与 AI 共建产物，用户可对 AI 建议做出接受/拒绝/修改反馈。

**典型应用：**
- 旅行规划师 (Travel Planner)

**设计原则：**
- AI 提供建议，用户决策
- 支持接受/拒绝/修改/跳过操作
- AI 根据用户反馈调整后续建议

## 🤖 模型配置

### 本地模型

通过 [Ollama](https://ollama.ai) 运行本地模型：

```bash
# 安装并运行模型
ollama pull qwen2.5:7b
ollama serve
```

在 `config/models.json` 中配置（`api_key` 留空表示使用本地模式）：

```json
{
    "active_provider": "local_ollama",
    "providers": {
        "local_ollama": {
            "name": "Ollama 本地",
            "model": "qwen2.5:7b",
            "api_url": "http://localhost:11434/v1",
            "api_key": "",
            "max_tokens": 4096,
            "timeout": 420
        }
    }
}
```

### 云端模型

支持 OpenAI 兼容 API（OpenAI、通义千问、智谱等）：

```json
{
    "active_provider": "openai",
    "providers": {
        "openai": {
            "name": "OpenAI",
            "model": "gpt-4o-mini",
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-your-api-key-here",
            "max_tokens": 4096,
            "timeout": 120
        }
    }
}
```

### 运行时切换

通过 API 热切换模型，无需重启服务：

```bash
# 查看当前可用模型
curl http://localhost:8000/api/models/providers

# 切换到指定模型
curl -X POST http://localhost:8000/api/models/switch/openai
```

## 🛠️ AI 应用构建器

ModelPlay 内置 **AI 应用构建器**，让你无需手写代码即可生成新应用：

1. **描述需求**：用自然语言描述你想要的应用
2. **方案设计**：AI 分析需求并设计应用方案
3. **代码生成**：基于开发模板生成完整可运行代码
4. **一键运行**：保存到 `pages/` 目录，立即在游戏中心启动

### 开发模板

构建器基于 `src/temple.py` 开发模板生成代码。模板包含：

- 配置区（API 地址、应用元数据、游戏提示词）
- 状态初始化（session_state 管理）
- 控制函数（`start_game` / `make_action` / `get_summary` / `reset_game`）
- UI 三态（`not_started` / `playing` / `ended`）
- 侧边栏日志

模板中 `# !!!` 标记的代码必须保留，`# >>>` 标记的部分需要替换为应用特定逻辑。

## 📊 Token 用量管理

平台提供每日 Token 使用量追踪与限额管理：

### 配置限额

编辑 `config/app.json`：

```json
{
    "api_base_url": "http://localhost:8000",
    "frontend_timeout": 480,
    "daily_token_limit": 1000000
}
```

设置 `daily_token_limit` 为 `0` 表示不限制。

### API 接口

```bash
# 获取今日用量
curl http://localhost:8000/api/usage

# 重置今日用量（管理员）
curl -X POST http://localhost:8000/api/usage/reset
```

### 自动重置

每日 00:00 自动重置计数。超过限额时，模型调用将被暂停并返回提示。

## 📁 项目结构

```
modelplay/
├── app.py                    # Streamlit 主页
├── src/
│   ├── api_server.py         # FastAPI 后端服务
│   ├── app_config.py         # 应用配置管理
│   ├── llm.py                # LLM 客户端封装
│   ├── model_config.py       # 模型供应商配置
│   ├── prompts.py            # 提示词管理
│   ├── temple.py             # 应用开发模板
│   ├── theme.py              # 明暗主题样式
│   ├── language.py           # 中英文 i18n
│   └── token_tracker.py      # Token 用量追踪
├── pages/
│   ├── App_Builder.py        # AI 应用构建器
│   ├── game_hub.py           # 游戏大厅
│   ├── Tic_Tac_Toe.py        # 井字棋
│   ├── Chess.py              # 国际象棋
│   ├── Number_Fill_zh.py     # 填数字对战
│   ├── Number_Guess_Game.py  # 猜数字
│   ├── rps_game.py           # 石头剪刀布
│   ├── English_Tutor.py      # 英语口语辅导
│   ├── Travel_Planner.py     # 旅行规划师
│   ├── modelplay_docs.py     # 项目文档
│   └── modelplay_about.py    # 关于页面
└── config/
    ├── app.json              # 应用配置
    ├── models.json           # 模型配置
    └── token_usage.json      # Token 使用统计
```

## 🔌 API 文档

启动后端后，访问 `http://localhost:8000/docs` 查看完整的 Swagger API 文档。

### 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/game/start` | POST | 启动新游戏会话 |
| `/api/game/move` | POST | 发送动作并获取 AI 回应 |
| `/api/game/summary/{id}` | POST | 生成对战总结 |
| `/api/game/end/{id}` | POST | 结束游戏会话 |
| `/api/usage` | GET | 获取今日 Token 用量 |
| `/api/usage/reset` | POST | 重置今日用量 |
| `/api/models/providers` | GET | 列出所有模型供应商 |
| `/api/models/switch/{name}` | POST | 切换模型供应商 |
| `/api/models/test/{name}` | POST | 测试模型连通性 |

## 🧩 开发新应用

### 方式一：使用 AI 构建器

1. 在主页进入「游戏中心」
2. 打开「AI 应用构建器」
3. 用自然语言描述需求
4. 等待 AI 生成代码
5. 在游戏中心启动生成的应用

### 方式二：手动开发

1. 复制 `src/temple.py` 到 `pages/` 目录
2. 重命名为你的应用名（如 `My_Game.py`）
3. 替换 `# >>>` 标记的部分
4. 保留 `# !!!` 标记的框架代码
5. 在游戏中心启动

### 核心规则

1. **状态生成在前端**：目标数字、棋盘等状态必须用 `random.randint()` 在前端生成，不能从后端获取
2. **只发送用户请求**：前端只能发送 `player: "user"` 的请求
3. **game_prompt 指定格式**：必须明确要求模型返回 JSON 格式
4. **模型只出招**：胜负判定、比分管理必须在前端实现，不要让模型自导自演

## 📜 许可证

MIT License