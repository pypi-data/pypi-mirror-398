"""
Telegram RAG Bot - Production-ready FAQ bot with Russian LLMs.

A configurable Telegram chatbot powered by:
- Multi-LLM Orchestrator (GigaChat, YandexGPT)
- LangChain RAG chains
- FAISS/OpenSearch vector stores
- Flexible embeddings (Local, GigaChat, Yandex)
"""

__version__ = "0.8.3"
__author__ = "Mikhail Malorod"
__license__ = "MIT"

from telegram_rag_bot.main import main

__all__ = ["main", "__version__"]
