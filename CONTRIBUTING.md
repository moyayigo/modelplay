# Contributing to ModelPlay

Thanks for your interest in contributing to ModelPlay! We welcome contributions from the community. This guide will help you get started.

## 🎯 Ways to Contribute

### 1. **Report Bugs**
Found a bug? [Open an issue](https://github.com/moyayigo/modelplay/issues) and describe:
- What you were doing
- What happened
- What you expected to happen
- Your environment (OS, Python version, model used)

### 2. **Suggest Features**
Have an idea? We'd love to hear it! Open an issue with the `[Feature Request]` tag.

### 3. **Submit Code**
Want to code? Here's how:

#### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/modelplay.git
cd modelplay

# Create a branch for your feature
git checkout -b feature/your-feature-name

# Install dependencies
pip install streamlit fastapi uvicorn requests pydantic

# Start developing...
```

#### Development Guidelines

**Adding New Apps:**
1. Copy `src/temple.py` to `pages/` directory
2. Rename to your app name (e.g., `pages/My_Game.py`)
3. Replace sections marked with `# >>>` 
4. Preserve framework code marked with `# !!!`
5. Follow the three application patterns:
   - **Games**: Frontend manages score, win/loss; model only "makes moves"
   - **Courses**: AI asks questions, evaluates answers, provides feedback
   - **Collaborative**: AI suggests, user decides (accept/reject/edit)

**Key Rules:**
- Generate random states in frontend (targets, boards, etc.), not backend
- Only send requests with `player: "user"` from frontend
- `game_prompt` must clearly specify JSON response format
- Don't let the model self-direct game logic (model only responds to player moves)

**Example Game Structure:**
```python
# >>> SECTION: Replace these with your game logic

def start_game():
    """Initialize game state"""
    st.session_state.target = random.randint(1, 100)
    st.session_state.guesses = 0

def make_action(user_input):
    """Process player move and get AI response"""
    # Send to backend, backend returns AI move
    pass

def get_summary():
    """Generate game summary/report"""
    pass

# !!! SECTION: Keep framework code intact
```

#### Code Style
- Follow PEP 8 Python conventions
- Add comments for complex logic
- Keep functions focused and modular
- Test locally before submitting PR

#### Submitting a Pull Request
1. Push your branch to your fork
2. Open a PR against `main` branch
3. Describe what your changes do and why
4. Link any related issues
5. Wait for review and feedback

### 4. **Improve Documentation**
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve README or API docs
- Translate content to other languages

### 5. **Add Translations**
Help translate ModelPlay to more languages! Current support: English, Chinese (Simplified)

## 🏗️ Project Structure

```
modelplay/
├── app.py                    # Streamlit homepage
├── src/
│   ├── api_server.py         # FastAPI backend
│   ├── llm.py                # LLM client
│   ├── model_config.py       # Model provider config
│   ├── prompts.py            # Prompt management
│   ├── temple.py             # App template (for developing new apps)
│   └── ...
├── pages/                    # Streamlit pages (apps)
├── config/                   # Configuration files
└── tests/                    # Tests (if any)
```

## 🧪 Testing

Before submitting a PR:
1. Test your app locally with at least one LLM backend (local Ollama or cloud API)
2. Verify UI looks good in light and dark themes
3. Check that error messages are helpful
4. Test on both desktop and mobile (if applicable)

## 📋 PR Checklist

- [ ] My code follows PEP 8 style guidelines
- [ ] I've tested my changes locally
- [ ] I've updated documentation if needed
- [ ] My PR description clearly explains the changes
- [ ] I've linked related issues
- [ ] No breaking changes (or documented if needed)

## 🚫 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Welcome different perspectives
- Help others learn

## ❓ Questions?

- Open an issue with `[Question]` tag
- Check existing issues for similar questions
- Discuss in GitHub Discussions (coming soon)

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Happy contributing!** 🎉

We're excited to have you join the ModelPlay community!
