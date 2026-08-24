import streamlit as st

st.set_page_config(page_title="开发文档", page_icon="📖", layout="wide", initial_sidebar_state="collapsed")

st.title("📖 ModelPlay 游戏开发文档")
st.caption("本文档面向开发者，介绍如何基于 ModelPlay 框架快速开发一个新的 AI 对战游戏")

# ================= 1. 架构概览 =================
st.header("1. 架构概览")

st.markdown("""
ModelPlay 采用**前后端分离**架构，核心设计理念是**游戏与系统解耦**：

```
┌──────────────────────────────────────────────────────┐
│                   Streamlit 前端                      │
│  (游戏页面: pages/Tic_Tac_Toe.py 等)                  │
│  - 渲染 UI / 棋盘 / 按钮                              │
│  - 管理本地状态 (session_state)                       │
│  - 发送 HTTP 请求到后端                               │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP REST API
                     ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI 后端 (api_server.py)         │
│  - 会话管理 (game_sessions)                           │
│  - 提示词组装 + LLM 调用                              │
│  - JSON 解析 & 响应格式化                             │
│  - 游戏总结生成                                       │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              LLM 层 (llm.py + model_config.py)       │
│  - 本地模型 (Ollama) 或 远程 API                      │
│  - 统一的 OpenAI-compatible 接口                      │
│  - 自动认证判断                                       │
└──────────────────────────────────────────────────────┘
```

**关键设计原则**：
- 游戏页面**只关心 UI 和交互**，不直接操作 LLM
- 后端 API 是**通用的**，不绑定任何特定游戏
- 游戏规则通过 `game_prompt` 参数**注入**，后端不感知游戏细节
- 游戏数据结构 (action / board) 采用**通用字典格式**，由游戏自行约定
""")

# ================= 2. 项目结构 =================
st.header("2. 项目结构")

code_block = """
modelplay/
├── index.py                  # 主页 (游戏启动器)
├── config/
│   └── models.json           # 模型 Provider 配置文件
├── src/
│   ├── api_server.py         # FastAPI 后端 (游戏 API + 模型管理 API)
│   ├── llm.py                # LLMClient (LLM 调用封装)
│   ├── model_config.py       # 模型配置管理器
│   ├── prompts.py            # PromptManager (系统提示词生成)
│   └── theme.py              # 主题 CSS 定义
└── pages/
    ├── Tic_Tac_Toe.py        # 井字棋游戏 (参考模板)
    ├── Number_Fill_zh.py     # 填数字游戏
    ├── game_hub.py           # 游戏大厅
    ├── modelplay_docs.py     # 本文档
    └── ...
"""
st.code(code_block, language="bash")

# ================= 3. API 通信协议 =================
st.header("3. API 通信协议")

st.subheader("3.1 通用数据结构")

st.markdown("""
系统使用统一的通用数据结构，所有游戏必须遵循以下格式：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | str | 会话唯一标识 (8位 UUID) |
| `player` | str | `"user"` 或 `"assistant"` |
| `action` | Any | 游戏动作，格式由游戏自行定义 |
| `board` | dict | 棋盘/状态，格式由游戏自行定义 |
| `status` | str | `"not_started"` / `"playing"` / `"ended"` / `"error"` |
| `message` | str | 可读的消息文本 |
""")

st.subheader("3.2 API 端点一览")

api_table = """
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /api/game/start | 启动新游戏，创建会话 |
| POST | /api/game/move | 发送玩家/模型动作 |
| GET  | /api/game/status/{session_id} | 查询会话状态 |
| POST | /api/game/end/{session_id} | 结束游戏 |
| POST | /api/game/summary/{session_id} | 生成对战策略分析 |
| GET  | /api/models/providers | 列出所有模型 Provider |
| POST | /api/models/switch/{name} | 切换激活的 Provider |
| POST | /api/models/add | 新增 Provider |
| DELETE | /api/models/delete/{name} | 删除 Provider |
| POST | /api/models/test/{name} | 测试 Provider 连通性 |
"""
st.markdown(api_table)

st.subheader("3.3 启动游戏")

st.markdown("""
**请求：**
```json
POST /api/game/start
{
    "game_type": "tic_tac_toe",
    "game_prompt": "你正在与用户玩井字棋..."
}
```

**响应：**
```json
{
    "session_id": "a340eb8f",
    "player": "system",
    "action": null,
    "board": {"state": null, "turn": "user"},
    "status": "started",
    "message": "游戏已启动，会话ID: a340eb8f"
}
```

**说明：**
- `game_type`：游戏类型标识，用于总结时显示
- `game_prompt`：游戏规则说明，会作为系统提示注入模型上下文
- 返回的 `session_id` 必须在后续所有请求中使用
""")

st.subheader("3.4 发送动作（核心接口）")

st.markdown("""
**请求：**
```json
POST /api/game/move
{
    "session_id": "a340eb8f",
    "player": "user",
    "action": {"row": 1, "col": 0, "mark": "X"},
    "board": {"state": [["","",""],["X","",""],["","",""]], "turn": "model"},
    "status": "playing"
}
```

**响应：**
```json
{
    "session_id": "a340eb8f",
    "player": "assistant",
    "action": {"player": "assistant", "row": 0, "col": 2},
    "board": {"state": {"player": "assistant", "row": 0, "col": 2}, "turn": "user"},
    "status": "playing",
    "message": "模型回应: {'player': 'assistant', 'row': 0, 'col': 2}"
}
```

**关键规则：**
1. `player` 必须为 `"user"`，后端只接受玩家发起的请求
2. 后端会自动将 `action`、`board` 内容追加到对话历史
3. 模型根据历史和游戏规则生成新的 `action`，解析后返回
4. 响应中的 `action` 字段为 `None` 表示模型未能生成有效操作
""")

st.subheader("3.5 生成对战总结")

st.markdown("""
**请求：**
```json
POST /api/game/summary/{session_id}
```

**响应：**
```json
{
    "session_id": "a340eb8f",
    "strategic_analysis": "模型选择了已占用的格子..."
}
```

**说明：**
- 需在游戏结束后调用
- 后端使用 `strategic_analysis` 作为 prompt 要求模型返回策略分析
- 返回的 JSON 中 `strategic_analysis` 字段即为分析结果
""")

# ================= 4. 游戏开发模板 =================
st.header("4. 游戏开发模板")

st.markdown("""
以下是一个最小化的游戏开发模板，展示了所有必须的组件。请对照 Tic_Tac_Toe.py 作为完整参考。
""")

st.subheader("4.1 基本骨架")

template_code = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
from src.theme import get_theme_css
from src.app_config import get_api_base_url, get_frontend_timeout

# ============ 配置 ============
API_BASE_URL = get_api_base_url()  # 从 config/app.json 读取
FRONTEND_TIMEOUT = get_frontend_timeout()  # 从 config/app.json 读取
GAME_TYPE = "my_game"

GAME_PROMPTS = {
    "my_game": """在这里写你的游戏规则，告诉模型如何玩这个游戏。
必须明确：
1. 模型扮演的角色
2. 游戏棋盘/状态的表示方式
3. 胜负条件
4. 返回的 JSON 格式""",
}

GAME_META = {
    "title": "我的游戏",
    "icon": "🎮",
    "description": "游戏描述",
}

# ============ 页面配置 ============
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.set_page_config(
    page_title="我的游戏",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="auto",
)
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# ============ 状态初始化 ============
# 所有状态变量必须在首次使用前初始化
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "status" not in st.session_state:
    st.session_state.status = "not_started"  # not_started | playing | ended
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "game_summary" not in st.session_state:
    st.session_state.game_summary = None
# ... 游戏特有的状态变量

# ============ 辅助函数 ============
def add_log(message, is_user=True):
    color = "#3498db" if is_user else "#e74c3c"
    icon = "👤" if is_user else "🤖"
    st.session_state.game_log.append({"message": message, "color": color, "icon": icon})

# ============ 游戏控制函数 ============
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
        st.session_state.status = "playing"
        st.session_state.game_log = []
        add_log(f"🎮 游戏开始", is_user=False)
    except requests.exceptions.RequestException as e:
        st.error(f"启动游戏失败: {str(e)}")

def make_action(user_action):
    """发送玩家动作到后端，获取模型回应。返回 True 表示成功。"""
    request_data = {
        "session_id": st.session_state.session_id,
        "player": "user",
        "action": user_action,
        "board": {"state": st.session_state.board, "turn": "model"},
        "status": "playing",
    }

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/game/move",
                json=request_data,
                timeout=FRONTEND_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            model_action = data.get("action")

            # ============ 验证模型返回 ============
            if model_action is None:
                if attempt < max_attempts - 1:
                    continue
                break

            # TODO: 在此处验证模型动作的合法性
            # 例如：检查坐标是否有效、格子是否已占用等
            # 如果非法：构造 retry_prompt，continue 到下一次重试

            # ============ 合法：应用模型动作 ============
            # TODO: 将 model_action 应用到本地棋盘
            add_log(f"模型回应: {model_action}", is_user=False)
            return True

        except requests.exceptions.Timeout:
            st.error("⏱️ 请求超时")
            return False
        except requests.exceptions.RequestException as e:
            st.error(f"请求失败: {str(e)}")
            return False

    # 重试耗尽：强制结束游戏
    st.session_state.status = "ended"
    st.session_state.is_draw = True
    st.session_state.final_result = {"reason": "模型多次无效响应"}
    add_log(f"😵 模型连续 {max_attempts} 次无效响应，游戏结束", is_user=False)
    return False

# ============ 游戏 UI ============
if st.session_state.status == "not_started":
    # 开始界面
    if st.button("开始游戏"):
        start_game()
        st.rerun()

elif st.session_state.status == "playing":
    # 游戏进行中界面
    # TODO: 渲染你的棋盘/交互 UI

elif st.session_state.status == "ended":
    # 游戏结束界面
    # TODO: 显示结果、总结、重新开始按钮

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📋 游戏日志")
    for log in reversed(st.session_state.game_log):
        with st.expander(f"{log['icon']} {log['message'][:50]}", expanded=False):
            st.markdown(log["message"])
    if st.session_state.session_id:
        st.caption(f"会话ID: {st.session_state.session_id}")
'''
st.code(template_code, language="python")

# ================= 5. 关键实践指南 =================
st.header("5. 关键实践指南")

st.subheader("5.1 游戏提示词 (game_prompt) 编写")
st.markdown("""
**好的提示词应该包含：**
1. **角色定位**：模型扮演什么角色（如 "你执 O"）
2. **状态表示**：棋盘/状态如何编码（如 "3x3 数组，索引 0-2"）
3. **回合规则**：谁先谁后，轮流规则
4. **胜负条件**：获胜条件和平局条件
5. **输出格式**：必须严格的 JSON 格式，给出示例

**反模式：**
- ❌ 不要在 game_prompt 中加入与游戏无关的内容
- ❌ 不要让模型返回自然语言描述，必须要求 JSON
- ❌ 不要省略示例，模型更容易遵循有示例的格式
""")

st.subheader("5.2 超时设置")
st.markdown("""
```
FRONTEND_TIMEOUT (前端)  >  API 后端 timeout  >  LLM timeout
```

- 前端 `FRONTEND_TIMEOUT` 应设为 **480 秒**（8 分钟）
- 后端默认 LLM timeout 为 **420 秒**
- 前端超时必须大于后端，否则前端会先于模型响应超时

**常见错误：**
- 前端超时设为 60 秒，但模型推理需要 2 分钟 → 前端先超时，模型仍在生成
""")

st.subheader("5.3 模型重试机制")
st.markdown("""
当模型返回非法动作（占用格子、越界、格式错误等）时，应实现重试：

1. **最多重试 5 次**，每次附带更多提示信息
2. **最后一次仍失败** → 使用 `break` 跳出循环（不是 `return`）
3. **循环外处理**：设置 `status = "ended"` 强制结束游戏

```python
max_attempts = 5
for attempt in range(max_attempts):
    # ... 发起请求、验证 ...
    if attempt < max_attempts - 1:
        continue  # 重试
    break       # ← 关键：跳出循环，执行下方的强制结束逻辑

# 循环外：强制结束
st.session_state.status = "ended"
st.session_state.final_result = {"reason": "..."}
```

**常见陷阱：**
- ❌ 在最后一次尝试用 `return False` → 循环外的结束逻辑不执行
- ❌ 忘记在失败时设置 `status = "ended"` → 用户看到空页面
""")

st.subheader("5.4 状态管理")
st.markdown("""
**必须使用 `st.session_state` 存储所有跨 rerun 的状态：**

```python
# ✅ 正确：初始化检查
if "board" not in st.session_state:
    st.session_state.board = [["" for _ in range(3)] for _ in range(3)]

# ❌ 错误：直接赋值（每次 rerun 都会重置）
board = [["" for _ in range(3)] for _ in range(3)]
```

**重新开始游戏时的清理：**
```python
st.session_state.status = "not_started"
st.session_state.board = [...]
st.session_state.game_log = []
st.session_state.game_summary = None
# ... 重置所有状态
st.rerun()
```
""")

st.subheader("5.5 即时反馈（用户体验）")
st.markdown("""
**用户操作应立即反映到 UI：**

```python
# ✅ 正确：点击后立即更新 UI，再 rerun
if st.button(...):
    board[i][j] = "X"           # 立即更新
    st.session_state.pending_action = (i, j)
    st.session_state.turn = "model"
    st.rerun()                   # 重新渲染，显示用户动作

# ❌ 错误：等模型响应后才更新
# （用户会看到无变化，直到模型返回）
```
""")

# ================= 6. 模型配置 =================
st.header("6. 模型配置")

st.subheader("6.1 配置文件")
st.markdown("""
编辑 `config/models.json` 管理模型 Provider：

```json
{
    "active_provider": "local",
    "providers": {
        "local": {
            "name": "本地模型 (Ollama)",
            "model": "your-model-name",
            "api_url": "http://localhost:11434/v1",
            "api_key": "",
            "max_tokens": 8192,
            "timeout": 420
        },
        "remote": {
            "name": "远程 API",
            "model": "gpt-4o",
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-xxx...",
            "max_tokens": 4096,
            "timeout": 120
        }
    }
}
```

**自动模式判断：**
- `api_key` 为空 → 本地模式（不加 Authorization 头）
- `api_key` 有值 → 远程模式（自动加 `Bearer` 认证）
""")

st.subheader("6.2 管理 API")
st.markdown("""
| 操作 | API |
|------|-----|
| 查看所有 Provider | `GET /api/models/providers` |
| 切换 Provider | `POST /api/models/switch/{name}` |
| 添加 Provider | `POST /api/models/add?provider_name=x&name=x&model=x&api_url=x&api_key=x` |
| 删除 Provider | `DELETE /api/models/delete/{name}` |
| 测试连通性 | `POST /api/models/test/{name}` |
""")

# ================= 7. 调试技巧 =================
st.header("7. 调试技巧")

st.markdown("""
**1. 查看后端日志**
- api_server.py 会打印 `[DEBUG]` 开头的日志
- 包含：游戏提示词、用户 action、历史记录数、LLM 原始回复、解析结果

**2. 会话恢复**
- `GET /api/game/status/{session_id}` 可查询会话状态
- 前端调试时可直接调用此接口

**3. 常见问题排查**

| 问题 | 排查方向 |
|------|---------|
| 前端超时 | 检查 FRONTEND_TIMEOUT > LLM timeout |
| 模型不响应 | 检查后端是否启动、Provider 是否正确 |
| 模型选择非法位置 | 检查 game_prompt 是否明确、重试逻辑是否正确 |
| JSON 解析失败 | 检查模型返回格式、_extract_json_response 是否兼容 |
| 主题不生效 | 检查是否导入 theme 模块并调用 get_theme_css() |

**4. 打印调试**
在关键位置使用 `print()` 输出调试信息（后端直接打印到控制台）：
```python
print(f"[DEBUG] 收到响应: {data}")
print(f"[DEBUG] 模型动作: {model_action}")
```
""")

# ================= 8. 完整示例 =================
st.header("8. 参考实现")

st.markdown("""
**Tic_Tac_Toe.py** 是一个完整的参考实现，包含了所有最佳实践：

- ✅ 状态管理与初始化
- ✅ 游戏提示词注入
- ✅ 后端通信与重试机制
- ✅ 5 次重试后强制结束
- ✅ 用户操作即时反馈
- ✅ 游戏日志（侧边栏）
- ✅ 游戏总结生成
- ✅ 主题 CSS 应用
- ✅ 结果展示与重新开始

**Number_Fill_zh.py** 是另一个参考，展示了不同类型的游戏（数字推理类）。
""")

st.divider()
st.caption("📖 ModelPlay 开发文档 v1.0 | 基于 Tic_Tac_Toe 游戏开发经验总结")
