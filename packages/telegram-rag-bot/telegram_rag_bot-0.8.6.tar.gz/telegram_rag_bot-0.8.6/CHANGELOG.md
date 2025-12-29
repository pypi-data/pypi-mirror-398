# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.6] - 2025-12-27

### Added
- **Self-Contained Bundle Architecture** — Modes теперь хранятся как независимые bundles
  - Структура: `config/modes/<mode_name>/mode.yaml`, `system_prompt.md`, `faq.md`
  - Преимущества: независимые modes, версионирование через Git, масштабируемость
- **ModeLoader** — новый класс для динамической загрузки modes из директорий
  - Автоматическая валидация обязательных файлов (mode.yaml, system_prompt.md, faq.md)
  - Опциональная поддержка examples.yaml для few-shot examples
  - Graceful degradation (пропуск disabled modes)
  - Расположение: `telegram_rag_bot/mode_loader.py`
- **Автосоздание FAISS индексов** — индексы создаются автоматически при старте бота
  - Проверка существующих индексов (не пересоздаёт если уже есть)
  - Параллельная обработка всех modes
  - Подробное логирование (количество chunks для каждого mode)
- **Прогрев Embeddings модели** — модель загружается при старте (не при первом запросе)
  - Первый запрос пользователя работает быстро (~3 сек вместо 2.5 мин)
  - HuggingFace cache volume в Docker для сохранения моделей между пересборками
  - Graceful degradation если warmup упадёт (модель загрузится при первом запросе)
- **SSL сертификаты** — добавлены ca-certificates в Dockerfile
  - Исправляет SSL ошибки для GigaChat/Yandex APIs
  - Решает CERTIFICATE_VERIFY_FAILED ошибки

### Changed
- **config.yaml формат** — новый формат modes конфигурации
  ```yaml
  # БЫЛО (v0.8.5)
  modes:
    it_support:
      faq_file: "faqs/it_support.md"
      system_prompt: "You are IT support..."
  
  # СТАЛО (v0.8.6)
  modes:
    directory: "modes"
  ```
- **config_loader.py** — интеграция ModeLoader
  - Динамическая загрузка modes из bundles
  - Поддержка относительных и абсолютных путей
  - Функция `reload_config()` для hot updates
- **handlers.py** — обновлённые handlers
  - Автовыбор mode если только 1 активный (при `/start`)
  - Кнопки выбора для множественных modes
  - `/reload_faq` обновляет modes без перезапуска бота
- **main.py** — автосоздание FAISS индексов и прогрев embeddings
  - Индексы создаются для всех modes при старте
  - Embeddings модель прогревается перед запуском бота

### Fixed
- **FAISS индексы не создавались для новых modes** — теперь создаются автоматически
- **Дублирование пути** — исправлено `/app/config/config/modes` → `/app/config/modes`
- **Первый запрос timeout** — исправлено через прогрев embeddings модели при старте
- **Старые тесты не поддерживали новый формат** — обновлены test_config_loader.py и test_handlers.py

### Breaking Changes
- **Формат config.yaml изменён** — старый формат `modes: {it_support: {...}}` НЕ поддерживается
  - Обязательно использовать `modes.directory: "modes"`
- **Структура файлов изменена** — FAQ файлы должны быть в `config/modes/<mode_name>/faq.md`
  - System prompts в `config/modes/<mode_name>/system_prompt.md`
- **FAISS индексы пересоздаются** — при миграции удалить старые: `rm -rf .faiss_indices/*`
  - Новые создадутся автоматически при старте

### Migration
1. Обновить структуру modes:
   ```bash
   mkdir -p config/modes/it_support
   mv faqs/it_support.md config/modes/it_support/faq.md
   # Создать system_prompt.md и mode.yaml
   ```
2. Обновить config.yaml:
   ```yaml
   modes:
     directory: "modes"
   ```
3. Пересобрать Docker:
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```
4. Индексы создадутся автоматически при старте

### Tests
- **Новые тесты**: 14 тестов для ModeLoader (`tests/test_mode_loader.py`)
- **Обновлённые тесты**: test_config_loader.py, test_handlers.py (поддержка нового формата)
- **Coverage**: 76.11% (150 passed, 3 skipped, target 75% exceeded)

### Technical Details
- Новый файл: `telegram_rag_bot/mode_loader.py` (200+ строк)
- Изменённые файлы: config_loader.py, handlers.py, main.py, config.yaml
- Docker: добавлен huggingface_cache volume, ca-certificates в Dockerfile

## [0.8.5] - 2025-12-24

### Fixed
- **Critical**: Fixed `ValueError: Prompt must accept context` in RAG chains
  - Added `{context}` variable to prompt template in `RAGChainFactory.create_chain()`
  - LangChain's `create_stuff_documents_chain` requires explicit `{context}` variable
  - Context is automatically formatted from retrieved documents
  - Empty context is handled gracefully (LLM receives empty string)
  - Prompt template now includes `{context}` in human message
  - Format: "Контекст из базы знаний:\n\n{context}\n\nВопрос пользователя: {input}\n\nОтветь на основе контекста выше."
  - No breaking changes for end users
  - Existing chains will be recreated with new prompt on next `create_chain()` call

### Changed
- **Embeddings model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` → `sberbank-ai/sbert_large_nlu_ru`
  - Dimension: 384 → 1024
  - Reason: HuggingFace CDN blocked in Russia; Russian-optimized model yields higher FAQ accuracy
  - Benefit: Better relevance on Russian FAQs; accessible without VPN
- Auto-detect embeddings dimension instead of hardcoding; log model/dimension/device/size on load
- FAISS: Fail-fast dimension check on load with user-friendly guidance to run `/reload_faq`
- Error handling: Network/OOM specific messages for model loading

### Breaking Changes
- Existing FAISS indices built with 384-dim are incompatible (stored vs model dimension mismatch)
- Admin must run `/reload_faq` after updating to rebuild all indices with the new 1024-dim model

### Migration
1. Update to v0.8.5
2. Restart bot (`docker-compose restart bot`) and allow model download (~1.1 GB)
3. Run `/reload_faq` in Telegram to rebuild indices
4. Verify FAQ query (e.g., "Как сбросить пароль VPN?") returns relevant answer

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

## [0.8.4] - 2025-12-22

### Added
- **Pre-commit Tools** — Local quality checks before push
  - `scripts/pre-commit-check.sh` (bash, Linux/Mac/Git Bash)
  - `scripts/pre-commit-check.ps1` (PowerShell, Windows)
  - `Makefile` with 9 commands (help, format, lint, test, mypy, check, pre-commit, clean, install)
- **Developer Workflow** — One command (`make pre-commit`) runs all checks locally (10-20 seconds)
- **Documentation** — Updated README.md with "Development Setup" section
- **New Badges** — Added Tests, Coverage, Ruff, Pre-commit badges to README.md
- **Development Guide** — Created `Docs/DEVELOPMENT.md` with comprehensive development workflow

### Fixed
- **Technical Debt Resolution** — ruff 0 warnings (was 1), mypy 67 errors (was 87, 23% improvement)
  - `handlers.py`: Null checks for `update.message` and `effective_user` ([`638522d`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/638522d))
  - `config_loader.py`: `ProviderConfig` TypedDict for type safety ([`b7a4223`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/b7a4223))
  - `session_manager.py`: `get_session` return type → `Optional` ([`e5671a9`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/e5671a9))
  - `handlers.py`: LangChain response None checks ([`f12ab89`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/f12ab89))
  - `handlers.py`: Missing `await` for `rebuild_index` async call ([`f9be59d`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/f9be59d))
  - `__main__.py`: Removed f-string without placeholders ([`aa23405`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/aa23405))
- **Black Formatting** — 21 files auto-formatted ([`ff345f2`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/ff345f2))

### Changed
- **Quality Standards** — New/modified files MUST have type hints, null checks, docstrings, async/await
- **CI/CD Status** — All checks passing except mypy (non-blocking, 67 errors deferred to v0.9.0)

### Developer Experience
- **Time Saved** — 5-10 min per push (no CI/CD wait for trivial errors)
- **Fast Feedback** — Local checks in 10-20 seconds (vs 2-3 min CI/CD)
- **Auto-fix** — Black formatting runs automatically in pre-commit

### Non-Breaking Changes
- Remaining 67 mypy errors are non-critical (Dict[str, Any] generics, Optional imports)
- All functionality unchanged, only type annotations and guard clauses added
- Backward compatible with existing configurations

### Documentation
- `README.md` — Added "Development Setup" section with pre-commit workflow
- `PROJECT-TRUTH.md` — Updated with Day 20 achievements (pre-commit tools + technical debt)
- `Docs/DEVELOPMENT.md` — Created comprehensive development guide (new file)
- `Docs/QUALITY-GATES.md` — Updated current status (technical debt resolved)

### Commits
- [`aa23405`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/aa23405) — style(main): Remove f-string without placeholders
- [`638522d`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/638522d) — fix(handlers): Add null checks for update.message and effective_user
- [`b7a4223`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/b7a4223) — fix(config): Add TypedDict for ProviderConfig
- [`e5671a9`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/e5671a9) — fix(session): Change get_session return type to Optional
- [`f12ab89`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/f12ab89) — fix(handlers): Add None check for LangChain response
- [`f9be59d`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/f9be59d) — fix(handlers): Add missing await for async rebuild_index call
- [`cf35279`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/cf35279) — docs: Update mypy status (87 → 67 errors, top 20 fixed)
- [`084ac1e`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/084ac1e) — build: Add local quality checks (pre-commit scripts + Makefile)
- [`d412430`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/d412430) — docs: Update development setup with dev dependencies and quality checks
- [`ff345f2`](https://github.com/MikhailMalorod/telegram-bot-universal/commit/ff345f2) — style: Auto-format code with black (21 files)

## [0.8.5] - 2025-12-22

### Added
- **FeedbackCollector** — класс для сбора обратной связи от пользователей
  - Redis storage с TTL 90 дней (7776000 секунд)
  - Memory fallback при недоступности Redis
  - Методы: `save_feedback()`, `get_feedback()`
- **Команда `/help`** — инструкция для пользователей (Markdown формат)
  - Описание основных команд: `/start`, `/help`, `/feedback`
  - Примеры вопросов для бота
- **Команда `/feedback`** — запрос оценки качества ответа
  - Inline-кнопки рейтинга (1-5 звёзд)
  - Проверка наличия last_query/last_answer в session
- **Callback query handler** — обработка inline-кнопок
  - `feedback:{rating}` — сохранение оценки ответа
  - `action:feedback` — показ inline-кнопок рейтинга
  - `action:help` — показ help текста
  - `mode:{mode_name}` — переключение режима
- **Расширенный `/start`** — onboarding с 3 inline-кнопками:
  - "📚 IT Support FAQ" (переключение режима)
  - "💬 Оставить отзыв" (запрос feedback)
  - "❓ Помощь" (показать help)
- **Session storage** — сохранение `last_query` и `last_answer` для feedback

### Changed
- `telegram_rag_bot/handlers.py`:
  - Добавлен `handle_callback_query()` для обработки callback queries
  - Обновлен `cmd_start()` с inline-кнопками и расширенным welcome text
  - Обновлен `handle_message()` для сохранения last_query/last_answer
  - Добавлены методы `cmd_help()` и `cmd_feedback()`
- `telegram_rag_bot/main.py`:
  - Инициализация `FeedbackCollector` (после SessionManager)
  - Регистрация новых handlers (`/help`, `/feedback`, `CallbackQueryHandler`)
  - Передача `feedback_collector` в `TelegramHandlers`

### Tests
- `tests/test_feedback_collector.py` — новый файл (6 тестов):
  - `test_save_feedback_success`
  - `test_save_feedback_invalid_rating`
  - `test_save_feedback_memory_fallback`
  - `test_get_feedback`
  - `test_get_feedback_empty`
  - `test_get_feedback_memory_fallback`
  - `test_get_feedback_limit`
- `tests/test_handlers.py` — расширен (+6 тестов):
  - `test_cmd_help`
  - `test_cmd_feedback_no_history`
  - `test_cmd_feedback_with_history`
  - `test_handle_callback_query_feedback`
  - `test_handle_callback_query_action_help`
  - `test_handle_message_saves_session`
- `tests/conftest.py` — добавлены fixtures: `mock_callback_query`, `mock_feedback_collector`
- Coverage: 78%+ maintained

### Status
- ✅ Ready for 1-3 user pilot testing

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

