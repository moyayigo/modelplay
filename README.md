<div align="center">

<h1 align="center">🎮 ModelPlay</h1>

English / [简体中文](./README_zh.md)

</div>

> An LLM-powered AI interaction platform — let AI be your game opponent, learning tutor, or collaboration partner

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Introduction

**ModelPlay** is an AI interaction platform based on local Large Language Models (LLMs). It abstracts AI interactions into three typical patterns: **Battle Games**, **Interactive Courses**, and **Human-AI Collaboration**, providing a universal frontend/backend framework to quickly integrate any AI interaction scenario.

The platform includes a built-in **AI App Builder** — just describe your needs in natural language, and AI will automatically generate a complete application that conforms to the platform architecture.

### ✨ Key Features

- 🖥️ **Local First**: Supports local inference backends like Ollama / llama.cpp, data stays on your machine
- ☁️ **Cloud Compatible**: Compatible with OpenAI-compatible cloud services, just enter your API Key
- 🎮 **Universal Framework**: Fully decoupled frontend/backend, just define a Prompt to integrate new apps
- 🤖 **AI Builder**: Describe needs in natural language, AI auto-generates app code
- 📊 **Usage Tracking**: Daily token counting and quota management with visualization
- 🌗 **Dark/Light Theme**: Exquisite UI with dark/light themes and bilingual (Chinese/English)
- 🔧 **Modular**: Prompt manager and LLM interfaces can be independently replaced and extended

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Local model inference backend (Ollama / llama.cpp) or cloud API Key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/modelplay.git
cd modelplay

# 2. Install dependencies
pip install streamlit fastapi uvicorn requests pydantic

# 3. Configure model (edit config/models.json)
{
    "active_provider": "local_ollama",
    "providers": {
        "local_ollama": {
            "name": "Ollama Local",
            "model": "qwen2.5:7b",
            "api_url": "http://localhost:11434/v1",
            "api_key": "",
            "max_tokens": 4096,
            "timeout": 420
        }
    }
}

# 4. Start the backend service
python src/api_server.py

# 5. Start the frontend platform (new terminal)
streamlit run app.py
```

Open your browser at `http://localhost:8501` to start using.

## 🏗️ Three Application Types

ModelPlay supports three typical AI interaction patterns:

### 🎮 Battle Games (Game)

User and AI take turns competing. Frontend handles win/loss judgment and score management.

**Typical Applications:**
- Tic-Tac-Toe
- Rock-Paper-Scissors
- Number Guessing
- Chess

**Design Principles:**
- Model only "makes moves" (returns actions)
- Win/loss judgment, score management, and win condition checks are all in the frontend
- Don't let the model self-direct

### 📚 Interactive Courses (Course)

AI acts as a guide, proactively asking questions. Students answer and receive feedback.

**Typical Applications:**
- English Speaking Tutor

**Design Principles:**
- AI proactively asks questions to guide learning
- Provides instant feedback after student answers
- Generates a learning report after preset rounds

### 🤝 Human-AI Collaboration (Collaborative)

User and AI co-create deliverables. User can accept/reject/edit AI suggestions.

**Typical Applications:**
- Travel Planner

**Design Principles:**
- AI provides suggestions, user makes decisions
- Supports accept/reject/edit/skip operations
- AI adjusts subsequent suggestions based on user feedback

## 🤖 Model Configuration

### Local Models

Run local models via [Ollama](https://ollama.ai):

```bash
# Install and run a model
ollama pull qwen2.5:7b
ollama serve
```

Configure in `config/models.json` (leave `api_key` empty for local mode):

```json
{
    "active_provider": "local_ollama",
    "providers": {
        "local_ollama": {
            "name": "Ollama Local",
            "model": "qwen2.5:7b",
            "api_url": "http://localhost:11434/v1",
            "api_key": "",
            "max_tokens": 4096,
            "timeout": 420
        }
    }
}
```

### Cloud Models

Supports OpenAI-compatible APIs (OpenAI, Qwen, Zhipu, etc.):

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

### Runtime Switching

Hot-switch models via API without service restart:

```bash
# List available models
curl http://localhost:8000/api/models/providers

# Switch to a specific model
curl -X POST http://localhost:8000/api/models/switch/openai
```

## 🛠️ AI App Builder

ModelPlay includes a built-in **AI App Builder** that lets you generate new apps without writing code:

1. **Describe Requirements**: Describe the app you want in natural language
2. **Design**: AI analyzes requirements and designs the app
3. **Code Generation**: Generates complete runnable code based on the template
4. **One-Click Run**: Saved to `pages/` directory, ready to run in the Games Hub

### Development Template

The builder generates code based on the `src/temple.py` template, which includes:

- Config section (API URL, app metadata, game prompt)
- State initialization (session_state management)
- Control functions (`start_game` / `make_action` / `get_summary` / `reset_game`)
- UI three states (`not_started` / `playing` / `ended`)
- Sidebar log

Code marked with `# !!!` must be preserved; parts marked with `# >>>` need to be replaced with app-specific logic.

## 📊 Token Usage Management

The platform provides daily token usage tracking and quota management:

### Configure Quota

Edit `config/app.json`:

```json
{
    "api_base_url": "http://localhost:8000",
    "frontend_timeout": 480,
    "daily_token_limit": 1000000
}
```

Set `daily_token_limit` to `0` for unlimited.

### API Endpoints

```bash
# Get today's usage
curl http://localhost:8000/api/usage

# Reset today's usage (admin)
curl -X POST http://localhost:8000/api/usage/reset
```

### Auto Reset

Counts auto-reset at 00:00 daily. When the quota is exceeded, model calls are suspended with a notification.

## 📁 Project Structure

```
modelplay/
├── app.py                    # Streamlit homepage
├── src/
│   ├── api_server.py         # FastAPI backend service
│   ├── app_config.py         # App config management
│   ├── llm.py                # LLM client wrapper
│   ├── model_config.py       # Model provider config
│   ├── prompts.py            # Prompt management
│   ├── temple.py             # App development template
│   ├── theme.py              # Dark/light theme styles
│   ├── language.py           # Chinese/English i18n
│   └── token_tracker.py      # Token usage tracking
├── pages/
│   ├── App_Builder.py        # AI App Builder
│   ├── game_hub.py           # Games Hub
│   ├── Tic_Tac_Toe.py        # Tic-Tac-Toe
│   ├── Chess.py              # Chess
│   ├── Number_Fill_zh.py     # Number Battle
│   ├── Number_Guess_Game.py  # Number Guessing
│   ├── rps_game.py           # Rock-Paper-Scissors
│   ├── English_Tutor.py      # English Speaking Tutor
│   ├── Travel_Planner.py     # Travel Planner
│   ├── modelplay_docs.py     # Project docs
│   └── modelplay_about.py    # About page
└── config/
    ├── app.json              # App config
    ├── models.json           # Model config
    └── token_usage.json      # Token usage stats
```

## 🔌 API Documentation

After starting the backend, visit `http://localhost:8000/docs` for full Swagger API docs.

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/game/start` | POST | Start a new game session |
| `/api/game/move` | POST | Send action and get AI response |
| `/api/game/summary/{id}` | POST | Generate battle summary |
| `/api/game/end/{id}` | POST | End a game session |
| `/api/usage` | GET | Get today's token usage |
| `/api/usage/reset` | POST | Reset today's usage |
| `/api/models/providers` | GET | List all model providers |
| `/api/models/switch/{name}` | POST | Switch model provider |
| `/api/models/test/{name}` | POST | Test model connectivity |

## 🧩 Developing New Apps

### Option 1: Using the AI Builder

1. Go to "Games Hub" from the homepage
2. Open "AI App Builder"
3. Describe your needs in natural language
4. Wait for AI to generate the code
5. Launch the generated app from the Games Hub

### Option 2: Manual Development

1. Copy `src/temple.py` to the `pages/` directory
2. Rename it to your app name (e.g., `My_Game.py`)
3. Replace the parts marked with `# >>>`
4. Preserve the framework code marked with `# !!!`
5. Launch from the Games Hub

### Core Rules

1. **State generation in frontend**: Target numbers, boards, etc. must be generated with `random.randint()` in the frontend, not fetched from the backend
2. **Only send user requests**: Frontend can only send requests with `player: "user"`
3. **game_prompt specifies format**: Must clearly require the model to return JSON format
4. **Model only makes moves**: Win/loss judgment and score management must be in the frontend; don't let the model self-direct

## 📜 License

MIT License