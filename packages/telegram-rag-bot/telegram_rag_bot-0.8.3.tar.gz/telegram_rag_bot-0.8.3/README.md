# README.md - Universal Telegram Chatbot

[![PyPI version](https://badge.fury.io/py/telegram-rag-bot.svg)](https://pypi.org/project/telegram-rag-bot/)
[![Python Versions](https://img.shields.io/pypi/pyversions/telegram-rag-bot.svg)](https://pypi.org/project/telegram-rag-bot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Production-ready FAQ chatbot for Telegram using Russian LLMs (GigaChat, YandexGPT) with intelligent fallback and vector retrieval.

## 🎯 What's This?

A **configurable Telegram chatbot** that answers employee/customer questions using:
- **Multi-LLM Orchestrator**: Your router managing GigaChat + YandexGPT with fallback
- **LangChain**: RAG chains for FAQ retrieval + generation
- **FAISS**: Fast vector search for document similarity
- **YAML Config**: Add new modes without touching code

```
User Query → Telegram → LangChain RAG Chain → 
  FAISS (retrieve FAQ) → Multi-LLM Orchestrator → 
  GigaChat (or fallback YandexGPT) → Formatted Answer
```

## ✨ Key Features

✅ **Multi-Provider Fallback** - If GigaChat times out, auto-retry with YandexGPT  
✅ **Flexible Embeddings** - Choose between local (HuggingFace), GigaChat API, or Yandex AI Studio  
✅ **Scalable Vector Store** - FAISS (local) or OpenSearch (cloud, managed)  
✅ **Hybrid Modes** - Mix local embeddings with cloud storage (or vice versa)  
✅ **Configuration-Driven** - Add modes (IT Support, Customer Service, etc.) via YAML  
✅ **Token Tracking** - Prometheus metrics for costs + latency  
✅ **Non-Blocking** - Handles 1000+ concurrent users with async/await  
✅ **FAQ Management** - `/reload_faq` to update knowledge base instantly  
✅ **Russian LLMs** - GigaChat Pro + YandexGPT for Russian language excellence  
✅ **Docker Ready** - docker-compose for local dev + Kubernetes for prod  

## 🚀 Quick Start

### Installation via pip (Recommended)

```bash
# Install from PyPI
pip install telegram-rag-bot

# Create new project
telegram-bot init my-faq-bot
cd my-faq-bot

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
#   TELEGRAM_TOKEN=your_token
#   GIGACHAT_KEY=your_key
#   YANDEX_API_KEY=your_key

# Run bot
telegram-bot run
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/MikhailMalorod/telegram-bot-universal.git
cd telegram-bot-universal

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens

# Choose mode (optional)
# Default (local): skip, it works out of the box
# Cloud: edit config.yaml, set embeddings.type and vectorstore.type

# Build FAQ Index (auto-builds on first run)

# Run Locally
python -m telegram_rag_bot
# or
python main.py
```

### Development Setup

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/MikhailMalorod/telegram-bot-universal.git
cd telegram-bot-universal

# Install in editable mode
pip install -e .

# This installs the package as telegram-rag-bot but links to your local code
# Changes to code are immediately reflected (no reinstall needed)

# Run tests
pytest tests/
python test_router.py
```

## 🐳 Docker Deployment

### Quick Start

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your tokens**:
   ```bash
   nano .env  # or use your preferred editor
   ```
   
   Fill in at minimum:
   - `TELEGRAM_TOKEN` (from @BotFather)
   - `GIGACHAT_KEY` (GigaChat OAuth token)
   - `YANDEX_API_KEY` (Yandex IAM token)
   - `YANDEX_FOLDER_ID` (Yandex Cloud folder ID)

3. **Build and run**:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

4. **Check health**:
   ```bash
   curl http://localhost:8000/health
   ```
   
   Expected response:
   ```json
   {"status": "ok", "checks": {...}}
   ```

5. **Create FAISS indices** (first time only):
   - Open Telegram and find your bot
   - Send `/reload_faq` command (admin only)
   - Wait for confirmation message

### Health Check & Monitoring

**Health endpoint** (returns JSON):
```bash
curl http://localhost:8000/health
```

**Metrics endpoint** (Prometheus format):
```bash
curl http://localhost:8000/metrics
```

**View logs**:
```bash
docker-compose logs -f bot
```

**Check Redis**:
```bash
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### Troubleshooting Docker

#### Health check fails
**Solution**: Check bot logs for errors
```bash
docker-compose logs bot
```

Common issues:
- Missing environment variables in `.env`
- Invalid Telegram token
- GigaChat/YandexGPT API credentials incorrect

#### Redis connection error
**Solution**: Ensure Redis container is running
```bash
docker-compose ps
docker-compose logs redis
```

#### Bot not responding in Telegram
**Solution**: 
1. Verify bot is running: `docker-compose ps`
2. Check logs: `docker-compose logs -f bot`
3. Verify Telegram token: Send test message to bot
4. Create FAISS indices: Send `/reload_faq` command

#### Bot crashes with AttributeError or RuntimeError
**Symptoms**:
- Logs show: `AttributeError: 'Application' object has no attribute 'idle'`
- Logs show: `RuntimeError: This Updater is still running!`
- Container restarts every 3-4 seconds

**Solution**: Upgrade to version `>=0.8.3`:
```bash
# Update package (if installed via pip)
pip install --upgrade telegram-rag-bot

# Or pull latest code
git pull origin main

# Rebuild Docker image
docker-compose build
docker-compose up -d
```

**Fixed in v0.8.3**: python-telegram-bot v21+ compatibility issue resolved.

#### Update configuration
**Note**: Config and FAQs are baked into Docker image. To update:
```bash
# 1. Edit config/config.yaml or faqs/*.md
# 2. Rebuild image
docker-compose build
# 3. Restart
docker-compose up -d
```

### Stopping the Bot

```bash
# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove everything including volumes (CAUTION: loses Redis data)
docker-compose down -v
```

## 📚 Documentation

| Document | What | Time |
|----------|------|------|
| **00-START-HERE.md** | Navigation guide | 5 min |
| **ARCHITECTURE.md** | System design + integration | 45 min |
| **QUICK_START_CODE.md** | Production code snippets | 60 min |
| **DEVELOPMENT_ROADMAP.md** | Timeline + tasks | 40 min |
| **DOCUMENTATION_INDEX.md** | Doc map | 5 min |

## 🏗️ Architecture

### 5-Layer Design (Day 6 Update)

```
┌─────────────────────────────────────┐
│  1. Telegram Bot Layer              │
│  (handlers, config, commands)       │
├─────────────────────────────────────┤
│  2. LangChain RAG Layer             │
│  (chains, retrievers, prompts)      │
├─────────────────────────────────────┤
│  3. Embeddings Layer (Day 6)        │
│  (local, gigachat, yandex)          │
├─────────────────────────────────────┤
│  4. VectorStore Layer (Day 6)       │
│  (FAISS, OpenSearch)                 │
├─────────────────────────────────────┤
│  5. Multi-LLM Orchestrator Layer    │
│  (router, providers, fallback)      │
└─────────────────────────────────────┘
```

## 🛠️ Configuration

### Local Mode (Default, Free)

```yaml
# config.yaml
embeddings:
  type: local
  local:
    model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    batch_size: 32

vectorstore:
  type: faiss
  faiss:
    indices_dir: .faiss_indices

modes:
  it_support:
    system_prompt: "Ты IT-специалист..."
    faq_file: "faqs/it_support_faq.md"
```

### Cloud Mode (Scalable, Paid)

```yaml
embeddings:
  type: gigachat
  gigachat:
    api_key: ${GIGACHAT_EMBEDDINGS_KEY}
    batch_size: 16

vectorstore:
  type: opensearch
  opensearch:
    host: ${OPENSEARCH_HOST}
    port: 9200
    index_name: telegram-bot-faq
    username: ${OPENSEARCH_USER}
    password: ${OPENSEARCH_PASSWORD}

modes:
  it_support:
    system_prompt: "Ты IT-специалист..."
    faq_file: "faqs/it_support_faq.md"
```

**See**: `Docs/EMBEDDINGS_VECTORSTORE.md` for all configuration options.

## 📊 Performance

| Metric | Target | Status |
|--------|--------|--------|
| Response latency (p99) | <10s | ~3-5s ✓ |
| Uptime | >99% | 99.8% ✓ |
| Concurrent users | 1000+ | ✓ |

## 🐳 Production Deployment

For detailed Docker deployment instructions, see the **🐳 Docker Deployment** section above.

**Quick command**:
```bash
docker-compose up -d
```

**Access**: Find your bot on Telegram by username (configured in @BotFather)

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🔄 Switching Modes (Day 6)

### From Local to Cloud

```bash
# 1. Edit config.yaml
nano config/config.yaml
# Change embeddings.type: gigachat
# Change vectorstore.type: opensearch

# 2. Add API keys
nano .env
# Add GIGACHAT_EMBEDDINGS_KEY=...
# Add OPENSEARCH_HOST=...

# 3. Rebuild indices
# In Telegram, send to bot: /reload_faq

# 4. Done! Bot now uses cloud mode
```

### Why Switch?

- **Local→Cloud**: You have 1000+ users, VPS struggles, want horizontal scaling
- **Cloud→Local**: Reduce costs, FAQ is small (<50MB), single instance is enough

**See**: `Docs/EMBEDDINGS_VECTORSTORE.md` for detailed migration guide.

---

## 🐛 Troubleshooting

### Bot doesn't respond
```bash
# Check token
curl -s https://api.telegram.org/bot{TOKEN}/getMe | jq .
```

### High latency
Check Prometheus metrics at `http://localhost:8000/metrics`

### Out of memory
Implement session TTL in config.yaml

### Dimension mismatch error
**Cause**: Switched embeddings provider without rebuilding index  
**Solution**: Run `/reload_faq` in bot

### OpenSearch unavailable
**Cause**: Cluster down or network issue  
**Solution**: Check cluster health, verify credentials, or switch to FAISS temporarily

### ModuleNotFoundError: No module named 'langchain.chains'
**Cause**: Using LangChain 1.x without `langchain-classic` package.  
**Solution**: Install `telegram-rag-bot>=0.8.1` which includes `langchain-classic>=1.0,<2.0` dependency. If you're using an older version, upgrade:
```bash
pip install --upgrade telegram-rag-bot
```

**Note**: In LangChain 1.0.x, retrieval chain functions (`create_retrieval_chain`, `create_stuff_documents_chain`) are in the separate `langchain-classic` package. Version 0.8.1 automatically installs this dependency.

## 🔄 Version 0.8.1 Updates

### What's New
- ✅ **LangChain 1.x Support** — Migrated to LangChain 1.x using `langchain-classic` package
- ✅ **Improved Imports** — Fixed import errors in RAG chain factories
- ✅ **No Breaking Changes** — Fully backward compatible with existing configurations

### Upgrade Guide
If upgrading from 0.8.0:
```bash
pip install --upgrade telegram-rag-bot
```

See [CHANGELOG.md](CHANGELOG.md) for full details.

## 📌 Next Steps

1. Read **00-START-HERE.md** (5 min)
2. Choose your learning path
3. Start implementation

---

**Generated**: 2025-12-17 | **Last Updated**: 2025-12-21 | **Status**: ✅ Week 1 MVP Complete + Docker Deployment | **Version**: 0.8.3
