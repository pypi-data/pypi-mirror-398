"""
Local embeddings provider using HuggingFace sentence-transformers.

This provider runs embeddings offline using pre-downloaded models.
No API keys required. Suitable for development and production.
"""

import asyncio
import logging
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from telegram_rag_bot.embeddings.base import EmbeddingsProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingsProvider(EmbeddingsProvider):
    """
    Local embeddings using HuggingFace sentence-transformers.
    
    Uses multilingual model by default: paraphrase-multilingual-MiniLM-L12-v2
    - Dimension: 384
    - Languages: 50+ including Russian
    - Speed: ~1000 docs/sec on CPU
    - Disk: ~500MB model download
    
    Attributes:
        model: HuggingFaceEmbeddings instance (lazy loaded).
        model_name: Name of the sentence-transformers model.
        batch_size: Batch size for processing (default: 32).
    """
    
    def __init__(self, config: dict):
        """
        Initialize local embeddings provider.
        
        Args:
            config: Configuration dictionary with keys:
                - model: Model name (e.g., "sentence-transformers/...")
                - batch_size: Optional batch size (default: 32)
        
        Example:
            >>> config = {
            ...     "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ...     "batch_size": 32
            ... }
            >>> provider = LocalEmbeddingsProvider(config)
        """
        self.model_name = config.get("model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.batch_size = config.get("batch_size", 32)
        self._model = None  # Lazy initialization
        self._dimension = 384  # For paraphrase-multilingual-MiniLM-L12-v2
        logger.info(f"LocalEmbeddingsProvider initialized with model: {self.model_name}")
    
    @property
    def model(self) -> HuggingFaceEmbeddings:
        """
        Lazy load embeddings model.
        
        Model is loaded on first use to avoid startup delay.
        
        Returns:
            HuggingFaceEmbeddings instance.
        """
        if self._model is None:
            logger.info(f"Loading embeddings model: {self.model_name} (~500MB download on first use)")
            self._model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': 'cpu'},  # Explicit CPU usage
                encode_kwargs={'normalize_embeddings': True}  # For better similarity search
            )
            logger.info(f"✅ Model loaded: {self.model_name}")
        return self._model
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents using HuggingFace model.
        
        Processes texts in batches for efficiency. Uses asyncio.to_thread()
        to avoid blocking event loop (HuggingFace is synchronous).
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors (384-dimensional floats).
            
        Raises:
            ValueError: If texts list is empty.
            RuntimeError: If model loading fails.
        """
        if not texts:
            raise ValueError("Cannot embed empty list of texts")
        
        logger.info(f"Embedding {len(texts)} documents with batch_size={self.batch_size}")
        
        # HuggingFace embed_documents is synchronous → use asyncio.to_thread
        embeddings = await asyncio.to_thread(
            self.model.embed_documents,
            texts
        )
        
        logger.info(f"✅ Embedded {len(texts)} documents → {len(embeddings)} vectors")
        return embeddings
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Embed single query text.
        
        Optimized for single text processing.
        
        Args:
            text: Single text string to embed.
            
        Returns:
            Embedding vector (384-dimensional floats).
            
        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        # HuggingFace embed_query is synchronous → use asyncio.to_thread
        embedding = await asyncio.to_thread(
            self.model.embed_query,
            text
        )
        
        return embedding
    
    @property
    def dimension(self) -> int:
        """
        Vector dimension for paraphrase-multilingual-MiniLM-L12-v2.
        
        Returns:
            384 (fixed for this model).
        """
        return self._dimension

