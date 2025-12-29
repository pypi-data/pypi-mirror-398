"""
RAG Chain Factory - creates and manages LangChain RAG chains.

Handles:
- Vector store abstraction (FAISS/OpenSearch)
- Embeddings abstraction (Local/GigaChat/Yandex)
- Document chunking
- Retrieval-augmented generation chains
"""

import asyncio
from pathlib import Path
from typing import Any, Dict
import logging

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.retrieval import (
    create_retrieval_chain,
)  # LangChain 1.x: using langchain-classic package
from langchain_classic.chains.combine_documents.stuff import (
    create_stuff_documents_chain,
)  # LangChain 1.x: using langchain-classic package

from telegram_rag_bot.embeddings.factory import EmbeddingsFactory
from telegram_rag_bot.vectorstore.factory import VectorStoreFactory
from telegram_rag_bot.vectorstore.local_faiss import LocalFAISSProvider
from telegram_rag_bot.vectorstore.cloud_opensearch import (
    OpenSearchProvider,
    OpenSearchRetriever,
)

logger = logging.getLogger(__name__)


class RAGChainFactory:
    """
    Factory for creating RAG chains with flexible vector stores.

    Handles:
    - Vector store abstraction (FAISS/OpenSearch)
    - Embeddings abstraction (Local/GigaChat/Yandex)
    - Document chunking
    - Retrieval-augmented generation chains
    """

    def __init__(
        self,
        llm: Any,  # LangChain LLM instance (MultiLLMOrchestrator or any BaseLLM)
        embeddings_config: Dict[str, Any],  # embeddings section from config.yaml
        vectorstore_config: Dict[str, Any],  # vectorstore section from config.yaml
        chunk_config: Dict[str, Any],  # chunk_size, chunk_overlap from config.yaml
        modes: Dict[str, Any],  # modes section from config.yaml
    ):
        """
        Initialize RAG factory.

        Args:
            llm: LangChain LLM instance (MultiLLMOrchestrator or any BaseLLM)
            embeddings_config: embeddings section from config.yaml
            vectorstore_config: vectorstore section from config.yaml
            chunk_config: dict with chunk_size, chunk_overlap
            modes: modes section from config.yaml
        """
        self.llm = llm
        self.chunk_size = chunk_config["chunk_size"]
        self.chunk_overlap = chunk_config["chunk_overlap"]
        self.modes = modes
        self.chains = {}  # Cache for RAG chains
        self.mode_locks = {}  # Concurrency locks per mode

        # Create embeddings provider
        logger.info("Creating embeddings provider...")
        try:
            self.embeddings_provider = EmbeddingsFactory.create(embeddings_config)
            logger.info(
                f"✅ Embeddings provider created: {type(self.embeddings_provider).__name__}"
            )
        except Exception as e:
            logger.error(f"Failed to create embeddings provider: {e}")
            raise

        # Create vector store provider
        logger.info("Creating vector store provider...")
        try:
            self.vectorstore_provider = VectorStoreFactory.create(
                vectorstore_config, self.embeddings_provider
            )
            logger.info(
                f"✅ Vector store provider created: {type(self.vectorstore_provider).__name__}"
            )
        except Exception as e:
            logger.error(f"Failed to create vector store provider: {e}")
            raise

    async def rebuild_index(self, mode: str, faq_file: str) -> None:
        """
        Rebuild vector index from FAQ file (async).

        Works with any vector store provider (FAISS, OpenSearch).
        Includes concurrency lock to prevent race conditions.

        Args:
            mode: Mode name (for index identification)
            faq_file: Path to FAQ markdown file

        Raises:
            FileNotFoundError: If FAQ file doesn't exist.
            ValueError: If documents list is empty.
            RuntimeError: If vectorization or storage fails.
        """
        # Validate FAQ file exists
        if not Path(faq_file).exists():
            raise FileNotFoundError(f"FAQ file not found: {faq_file}")

        # Concurrency lock per mode (prevent concurrent /reload_faq)
        if mode not in self.mode_locks:
            self.mode_locks[mode] = asyncio.Lock()

        async with self.mode_locks[mode]:
            logger.info(f"🔨 Building index for mode '{mode}' from {faq_file}")

            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
            )

            # Load documents (sync I/O → async thread)
            loader = TextLoader(faq_file, encoding="utf-8")
            documents = await asyncio.to_thread(loader.load)
            logger.info(f"Loaded {len(documents)} document(s)")

            # Validate documents not empty
            if not documents:
                raise ValueError(f"FAQ file is empty: {faq_file}")

            # Split into chunks
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")

            # Validate chunks not empty
            if not chunks:
                raise ValueError(f"No chunks created from FAQ file: {faq_file}")

            # Extract texts and metadatas
            texts = [doc.page_content for doc in chunks]
            metadatas = [
                {"source": faq_file, "mode": mode, **doc.metadata} for doc in chunks
            ]

            # Vectorize documents (batch processing with progress)
            logger.info(f"Vectorizing {len(texts)} chunks...")
            batch_size = getattr(self.embeddings_provider, "batch_size", 32)
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_embeddings = await self.embeddings_provider.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)

                # Progress logging for large FAQ files
                if len(texts) > 100:
                    logger.info(f"📊 Vectorizing: {i+len(batch)}/{len(texts)} chunks")

            logger.info(f"✅ Vectorized {len(texts)} chunks")

            # Store in vector store
            if isinstance(self.vectorstore_provider, LocalFAISSProvider):
                # FAISS: Use existing embeddings provider to avoid hardcoded models
                from langchain_community.vectorstores import FAISS

                if not hasattr(self.embeddings_provider, "model"):
                    raise ValueError(
                        "❌ Embeddings provider must expose model for FAISS indexing."
                    )
                embeddings_model = self.embeddings_provider.model

                # Create FAISS vectorstore (sync → async thread)
                vectorstore = await asyncio.to_thread(
                    FAISS.from_documents, chunks, embeddings_model
                )

                # Save to disk
                await asyncio.to_thread(
                    self.vectorstore_provider.save_index, vectorstore, mode
                )
                logger.info(f"✅ FAISS index saved for mode '{mode}'")

            elif isinstance(self.vectorstore_provider, OpenSearchProvider):
                # OpenSearch: Use new abstraction
                # First delete old index (if exists)
                await self.vectorstore_provider.delete_index(mode)

                # Add documents to OpenSearch
                await self.vectorstore_provider.add_documents(
                    texts, all_embeddings, metadatas, mode=mode
                )
                logger.info(f"✅ OpenSearch index created for mode '{mode}'")

            else:
                raise RuntimeError(
                    f"Unknown vector store provider: {type(self.vectorstore_provider)}"
                )

            # Clear cached chain for this mode
            if mode in self.chains:
                del self.chains[mode]
                logger.debug(f"Cleared cached chain for mode '{mode}'")

    def create_chain(self, mode: str) -> Any:
        """
        Create RAG chain for specific mode.

        Loads vector store index (FAISS or OpenSearch), creates retriever,
        and assembles retrieval chain with document chain.

        Supports both:
        - Local FAISS: Native LangChain retriever (optimized)
        - Cloud OpenSearch: Custom retriever (flexible)

        Args:
            mode: Mode name (e.g., "it_support")

        Returns:
            LangChain retrieval chain ready for queries

        Raises:
            ValueError: If mode not found in config or dimension mismatch.
            FileNotFoundError: If FAISS index not found.
            RuntimeError: If index loading fails.

        Example:
            >>> chain = factory.create_chain("it_support")
            >>> response = await chain.ainvoke({"input": "Как сбросить пароль VPN?"})
            >>> print(response["answer"])
        """
        # Check cache first (lazy loading)
        if mode in self.chains:
            logger.debug(f"Using cached chain for mode '{mode}'")
            return self.chains[mode]

        # Validate mode exists
        if mode not in self.modes:
            raise ValueError(
                f"Unknown mode: {mode}. Available: {list(self.modes.keys())}"
            )

        # Get mode config
        mode_config = self.modes[mode]
        system_prompt = mode_config["system_prompt"]
        faq_file = mode_config["faq_file"]

        # Create retriever based on vector store type
        if isinstance(self.vectorstore_provider, LocalFAISSProvider):
            # FAISS path: Use native LangChain retriever
            logger.info(f"Creating FAISS retriever for mode '{mode}'")

            try:
                vectorstore = self.vectorstore_provider.load_index(mode)
                retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
                logger.info(f"✅ Loaded FAISS index for mode '{mode}'")

            except FileNotFoundError as e:
                # Index not found → clear error message
                raise FileNotFoundError(
                    f"❌ FAISS index not found for mode '{mode}'.\n"
                    f"💡 Run /reload_faq to create index."
                ) from e

            except Exception as e:
                # Corrupted index → auto-rebuild (backward compatibility)
                logger.warning(
                    f"Index corrupted for mode '{mode}': {e}. "
                    f"Auto-rebuilding from {faq_file}..."
                )
                # Note: rebuild_index is now async, need to call from async context
                # For now, raise error and let user trigger /reload_faq
                raise RuntimeError(
                    f"❌ FAISS index corrupted for mode '{mode}'.\n"
                    f"💡 Run /reload_faq to rebuild index."
                ) from e

        elif isinstance(self.vectorstore_provider, OpenSearchProvider):
            # OpenSearch path: Use custom retriever
            logger.info(f"Creating OpenSearch retriever for mode '{mode}'")

            try:
                retriever = OpenSearchRetriever(
                    vectorstore_provider=self.vectorstore_provider,
                    embeddings_provider=self.embeddings_provider,
                    mode=mode,
                    k=3,
                )
                logger.info(f"✅ Created OpenSearch retriever for mode '{mode}'")

            except ValueError as e:
                # Dimension mismatch
                raise ValueError(
                    f"❌ Dimension mismatch for mode '{mode}'.\n"
                    f"{str(e)}\n"
                    f"💡 Run /reload_faq to rebuild index with correct dimension."
                ) from e

        else:
            raise RuntimeError(
                f"❌ Unknown vector store provider: {type(self.vectorstore_provider).__name__}"
            )

        # Create prompt template with {context} for RAG
        # LangChain requires {context} variable for create_stuff_documents_chain
        # create_stuff_documents_chain automatically formats retrieved documents into {context}
        # If no documents found, {context} will be empty string (LLM handles gracefully)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    "Контекст из базы знаний:\n\n{context}\n\n"
                    "Вопрос пользователя: {input}\n\n"
                    "Ответь на основе контекста выше.",
                ),
            ]
        )
        logger.debug(f"Created prompt template for mode '{mode}' with context support")

        # Create RAG chain
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        chain = create_retrieval_chain(retriever, document_chain)

        # Cache chain
        self.chains[mode] = chain
        logger.info(f"✅ RAG chain created for mode '{mode}'")

        return chain
