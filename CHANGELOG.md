# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- GitHub Discussions for community Q&A
- More language translations (Spanish, French, Japanese)
- Advanced prompt management UI
- Model benchmark/comparison tools
- Export game history and analytics
- WebSocket support for real-time interactions
- Docker support for easier deployment

## [0.1.0] - 2026-08-25

### Added
- Initial release of ModelPlay platform
- Three application patterns: Battle Games, Interactive Courses, Human-AI Collaboration
- Built-in AI App Builder for generating apps from natural language descriptions
- Support for local LLM backends (Ollama, llama.cpp)
- Support for cloud APIs (OpenAI, Qwen, Zhipu, any OpenAI-compatible service)
- Hot-swappable model providers without service restart
- Daily token usage tracking and quota management
- Dark/Light theme support
- Bilingual UI (English, Simplified Chinese)
- Streamlit frontend with beautiful interactive interface
- FastAPI backend with full REST API
- Swagger API documentation at `/docs`
- Project structure with modular design

### Included Apps
- **Games**: Tic-Tac-Toe, Chess, Rock-Paper-Scissors, Number Guessing, Number Fill
- **Courses**: English Speaking Tutor
- **Collaborative**: Travel Planner
- **Documentation**: ModelPlay Docs, About page

### Features
- Prompt management system
- Theme customization
- Language switching (Chinese/English)
- Token usage visualization
- Session state management
- Win/loss tracking and scoring
- Game summaries and learning reports

### Configuration
- `config/models.json` - Model provider configuration
- `config/app.json` - Application settings
- `config/token_usage.json` - Daily token tracking

### Documentation
- Comprehensive README with quick start guide
- API documentation with endpoint descriptions
- Project structure explanation
- Model configuration guide
- App development template and guidelines
- CONTRIBUTING.md for contributors
- CHANGELOG.md for version history
- CODE_OF_CONDUCT.md for community standards

---

## Version History Format

### [Version] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security vulnerability fixes

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues and contributing code.

## License

MIT License - see LICENSE file for details
