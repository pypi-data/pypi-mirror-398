"""
Local FAISS vector store provider.

This provider uses Facebook's FAISS library for local vector storage.
Stores indices on disk, no external dependencies required.
"""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from telegram_rag_bot.vectorstore.base import VectorStoreProvider

logger = logging.getLogger(__name__)


class LocalFAISSProvider(VectorStoreProvider):
    """
    Local FAISS vector store provider.
    
    Uses FAISS for fast similarity search with local disk storage.
    - Storage: Disk directory (e.g., .faiss_indices/{mode}/)
    - No external dependencies (offline)
    - Fast similarity search (optimized for CPU)
    
    Attributes:
        indices_dir: Base directory for FAISS indices.
        embeddings_provider: Embeddings provider for creating vectorstore.
    
    Note:
        This provider wraps existing FAISS logic from RAGChainFactory
        for backward compatibility.
    """
    
    def __init__(self, config: dict, embeddings_provider):
        """
        Initialize local FAISS provider.
        
        Args:
            config: Configuration dictionary with keys:
                - indices_dir: Base directory for indices (e.g., ".faiss_indices")
            embeddings_provider: EmbeddingsProvider instance (for dimension compatibility).
        """
        self.indices_dir = Path(config.get("indices_dir", ".faiss_indices"))
        self.embeddings_provider = embeddings_provider
        
        # Create indices directory
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFAISSProvider initialized (indices_dir: {self.indices_dir})")
    
    async def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Add documents to FAISS index and save to disk.
        
        Creates FAISS vectorstore from documents and saves to mode-specific directory.
        
        Args:
            texts: List of document texts.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dicts.
        
        Raises:
            ValueError: If lengths don't match.
            RuntimeError: If FAISS operations fail.
        
        Note:
            This method expects mode to be extracted from metadata["mode"]
            or to be called with mode context.
        """
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError(
                f"Length mismatch: texts({len(texts)}), embeddings({len(embeddings)}), "
                f"metadatas({len(metadatas)})"
            )
        
        # Note: This method is called from RAGChainFactory.rebuild_index()
        # which provides mode separately. We store index path determination
        # to the caller.
        logger.info(f"Creating FAISS index with {len(texts)} documents")
        
        # Create Document objects for FAISS
        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas)
        ]
        
        # FAISS.from_documents expects embeddings provider, not pre-computed embeddings
        # We need to use the LangChain-compatible embeddings wrapper
        # For now, we'll create a dummy wrapper that uses pre-computed embeddings
        # This is a workaround - actual implementation in RAGChainFactory
        # will use FAISS.from_documents() directly with HuggingFaceEmbeddings
        
        # Workaround: Store for later use in RAGChainFactory
        self._pending_documents = documents
        self._pending_embeddings = embeddings
        
        logger.info("✅ Documents prepared for FAISS indexing (actual indexing in RAGChainFactory)")
    
    def load_index(self, mode: str):
        """
        Load FAISS index from disk (synchronous).
        
        This method provides backward compatibility with existing RAGChainFactory code.
        Returns LangChain FAISS vectorstore object.
        
        Args:
            mode: Mode name (e.g., "it_support").
        
        Returns:
            FAISS vectorstore instance from LangChain.
        
        Raises:
            FileNotFoundError: If index doesn't exist.
            RuntimeError: If loading fails.
        """
        index_path = self.indices_dir / mode
        
        if not index_path.exists():
            raise FileNotFoundError(
                f"❌ FAISS index not found for mode '{mode}'.\n"
                f"📍 Expected: {index_path}\n"
                f"💡 Run /reload_faq to create index."
            )
        
        logger.info(f"Loading FAISS index from {index_path}")
        
        # Import here to avoid circular dependency
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        # Create embeddings instance (must match the one used during indexing)
        # For LocalEmbeddingsProvider, we know it uses HuggingFaceEmbeddings
        if hasattr(self.embeddings_provider, 'model'):
            # LocalEmbeddingsProvider
            embeddings = self.embeddings_provider.model
        else:
            # Fallback: create new instance (for backward compatibility)
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
        
        try:
            vectorstore = FAISS.load_local(
                str(index_path),
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"✅ FAISS index loaded for mode '{mode}'")
            return vectorstore
        
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load FAISS index: {e}") from e
    
    def save_index(self, vectorstore, mode: str):
        """
        Save FAISS index to disk (synchronous).
        
        Args:
            vectorstore: FAISS vectorstore instance from LangChain.
            mode: Mode name (e.g., "it_support").
        """
        index_path = self.indices_dir / mode
        vectorstore.save_local(str(index_path))
        logger.info(f"✅ FAISS index saved to {index_path}")
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents by query embedding.
        
        Note: For FAISS, we use LangChain's native as_retriever() instead
        of this method. This is here for interface completeness.
        
        Args:
            query_embedding: Query vector.
            k: Number of results.
        
        Returns:
            List of result dicts.
        
        Raises:
            NotImplementedError: Use load_index() + as_retriever() instead.
        """
        raise NotImplementedError(
            "For FAISS, use load_index() and vectorstore.as_retriever() instead.\n"
            "This method is only for OpenSearch custom retriever."
        )
    
    async def delete_index(self, mode: str) -> None:
        """
        Delete FAISS index for specific mode.
        
        Removes entire directory for mode.
        
        Args:
            mode: Mode name (e.g., "it_support").
        """
        index_path = self.indices_dir / mode
        
        if index_path.exists():
            # Use asyncio.to_thread for disk I/O
            await asyncio.to_thread(shutil.rmtree, str(index_path))
            logger.info(f"🗑️ Deleted FAISS index for mode '{mode}' at {index_path}")
        else:
            logger.warning(f"⚠️ FAISS index for mode '{mode}' not found (already deleted?)")

