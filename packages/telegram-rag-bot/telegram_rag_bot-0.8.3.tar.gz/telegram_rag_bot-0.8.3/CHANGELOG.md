# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-12-20

### Added
- Initial release
- Multi-LLM Orchestrator integration (GigaChat, YandexGPT)
- LangChain RAG chains with FAISS/OpenSearch vector stores
- Flexible embeddings (Local HuggingFace, GigaChat API, Yandex AI Studio)
- Telegram bot with /start, /mode, /reload_faq commands
- Session management (Redis + memory fallback)
- Config-driven FAQ modes (YAML)
- Health check endpoint for Docker/Kubernetes
- Structured logging (JSON/text formats)
- Prometheus metrics collection (query latency, active users, errors)
- CLI tool for project management

### Week 1 MVP Features
- Production-ready monitoring (health check + metrics)
- Graceful degradation patterns
- Comprehensive error handling
- Async/await architecture

### Fixed
- Environment variable validation for embeddings/vectorstore
- Graceful shutdown for OpenSearch connections
- Router providers type checking

## [0.8.0] - 2025-12-20

### Changed
- Migrated to LangChain 1.x compatibility
- Updated import paths for `create_retrieval_chain` and `create_stuff_documents_chain`
- Updated dependency: `langchain>=1.0`

### Technical Details
- No breaking changes for end users
- Backward compatible with existing configurations
- FAISS/OpenSearch indices remain unchanged

## [0.8.1] - 2025-12-20

### Fixed
- Fixed LangChain 1.x imports: using `langchain-classic` package for `create_retrieval_chain` and `create_stuff_documents_chain`
- Added `langchain-classic>=1.0,<2.0` dependency
- Синхронизирован requirements.txt с pyproject.toml (добавлены langchain>=1.0 и langchain-classic>=1.0,<2.0)
- Исправлены устаревшие пути bot/ → telegram_rag_bot/ в документации (Docs/)
- Исправлена версия prometheus-client в requirements.txt (==0.20.0 → >=0.19.0,<0.20.0)
- Исправлен устаревший импорт в тестах (bot.vectorstore → telegram_rag_bot.vectorstore)

### Technical Details
- In LangChain 1.0.x, retrieval chain functions are in separate `langchain-classic` package
- No breaking changes for end users
- Backward compatible with existing configurations

## [0.8.2] - 2025-12-21

### Added
- Docker infrastructure for staging deployment
  - `Dockerfile` with health check using curl
  - `docker-compose.yml` with bot + Redis services
  - `.dockerignore` for build optimization
- Environment templates for Docker and local development
  - `.env.example` (root) for Docker deployment
  - `telegram_rag_bot/templates/.env.example` for CLI init

### Fixed
- Corrected `.gitignore` path for FAISS indices (`.faiss_indices/` instead of `faiss_indices/`)

## [0.8.3] - 2025-12-21

### Fixed
- **Critical bug: Fixed python-telegram-bot v21+ compatibility**
  - Replaced deprecated `application.idle()` with asyncio.Event + signal handlers
  - Fixed shutdown sequence to prevent "This Updater is still running!" error
  - Added proper SIGTERM/SIGINT handling for graceful Docker shutdown
  - Added defensive checks before shutdown operations
  - Improved shutdown logging for better diagnostics
- Pinned `python-telegram-bot>=21.0,<22.0` to prevent breaking changes in v22

### Added
- Graceful shutdown support in Docker (SIGTERM handling)
- Detailed shutdown logging with emoji indicators

### Tested
- Docker deployment (startup + shutdown): ✅
- Container stability (no restart loops): ✅
- Health check endpoint: ✅
- Telegram polling: ✅

### Technical Details
- Fixed `AttributeError: 'Application' object has no attribute 'idle'`
- Fixed `RuntimeError: This Updater is still running!`
- Eliminated Docker restart loop (bot crashed every 3-4 seconds before fix)
- Shutdown sequence now: updater.stop() → app.stop() → app.shutdown()
- Signal handlers added for SIGTERM (Docker) and SIGINT (Ctrl+C)

## [Unreleased]

### Planned for 0.9.0
- Docker deployment (Dockerfile, docker-compose.yml)
- CI/CD pipeline (GitHub Actions)
- Unit tests (pytest framework)
- Comprehensive error handling (retry logic, circuit breaker)
- Connection pooling (Redis, OpenSearch)
- Token usage metric (state management)

---

## Version Update Checklist

When releasing a new version:

1. Update `telegram_rag_bot/__init__.py` (`__version__`)
2. Update `pyproject.toml` (`version` field)
3. Update `CHANGELOG.md` (add new version section)
4. Create git tag: `git tag -a v0.X.Y -m "Release v0.X.Y"`
5. Push tag: `git push origin v0.X.Y`
6. Create GitHub Release (GitHub Actions will auto-publish to PyPI)

