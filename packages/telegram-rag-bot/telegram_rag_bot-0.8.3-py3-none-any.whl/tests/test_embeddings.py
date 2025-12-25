"""
Unit tests for embeddings providers.

Tests LocalEmbeddingsProvider, GigaChatEmbeddingsProvider, YandexEmbeddingsProvider,
and EmbeddingsFactory.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from telegram_rag_bot.embeddings.factory import EmbeddingsFactory
from telegram_rag_bot.embeddings.local import LocalEmbeddingsProvider
from telegram_rag_bot.embeddings.gigachat import GigaChatEmbeddingsProvider
from telegram_rag_bot.embeddings.yandex import YandexEmbeddingsProvider


class TestEmbeddingsFactory:
    """Tests for EmbeddingsFactory."""
    
    def test_create_local_provider(self):
        """Test creating LocalEmbeddingsProvider."""
        config = {
            "type": "local",
            "local": {
                "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "batch_size": 32
            }
        }
        
        provider = EmbeddingsFactory.create(config)
        assert isinstance(provider, LocalEmbeddingsProvider)
        assert provider.model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        assert provider.batch_size == 32
    
    def test_create_gigachat_provider(self):
        """Test creating GigaChatEmbeddingsProvider."""
        config = {
            "type": "gigachat",
            "gigachat": {
                "api_key": "test-key",
                "model": "Embeddings",
                "batch_size": 16
            }
        }
        
        provider = EmbeddingsFactory.create(config)
        assert isinstance(provider, GigaChatEmbeddingsProvider)
        assert provider.api_key == "test-key"
        assert provider.batch_size == 16
    
    def test_create_yandex_provider(self):
        """Test creating YandexEmbeddingsProvider."""
        config = {
            "type": "yandex",
            "yandex": {
                "api_key": "test-key",
                "folder_id": "test-folder",
                "batch_size": 1
            }
        }
        
        provider = EmbeddingsFactory.create(config)
        assert isinstance(provider, YandexEmbeddingsProvider)
        assert provider.api_key == "test-key"
        assert provider.folder_id == "test-folder"
    
    def test_unknown_type_raises_error(self):
        """Test that unknown provider type raises ValueError."""
        config = {"type": "unknown"}
        
        with pytest.raises(ValueError, match="Unknown embeddings provider type"):
            EmbeddingsFactory.create(config)


class TestLocalEmbeddingsProvider:
    """Tests for LocalEmbeddingsProvider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        config = {
            "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "batch_size": 32
        }
        
        provider = LocalEmbeddingsProvider(config)
        assert provider.model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        assert provider.batch_size == 32
        assert provider.dimension == 384
    
    @pytest.mark.asyncio
    @patch('telegram_rag_bot.embeddings.local.asyncio.to_thread')
    async def test_embed_documents(self, mock_to_thread):
        """Test embedding multiple documents."""
        config = {"model": "test-model"}
        provider = LocalEmbeddingsProvider(config)
        
        # Mock HuggingFaceEmbeddings
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_to_thread.return_value = mock_embeddings
        
        texts = ["text1", "text2"]
        result = await provider.embed_documents(texts)
        
        assert result == mock_embeddings
        mock_to_thread.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embed_empty_list_raises_error(self):
        """Test that embedding empty list raises ValueError."""
        config = {"model": "test-model"}
        provider = LocalEmbeddingsProvider(config)
        
        with pytest.raises(ValueError, match="Cannot embed empty list"):
            await provider.embed_documents([])


class TestGigaChatEmbeddingsProvider:
    """Tests for GigaChatEmbeddingsProvider."""
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        config = {}
        
        with pytest.raises(ValueError, match="GIGACHAT_EMBEDDINGS_KEY not set"):
            GigaChatEmbeddingsProvider(config)
    
    @pytest.mark.asyncio
    @patch('telegram_rag_bot.embeddings.gigachat.httpx.AsyncClient')
    async def test_embed_documents(self, mock_client_class):
        """Test embedding documents via GigaChat API."""
        config = {
            "api_key": "test-key",
            "model": "Embeddings",
            "batch_size": 2
        }
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2], "index": 0},
                {"embedding": [0.3, 0.4], "index": 1}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GigaChatEmbeddingsProvider(config)
        provider._access_token = "test-token"  # Skip auth
        
        texts = ["text1", "text2"]
        result = await provider.embed_documents(texts)
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
    
    def test_dimension(self):
        """Test dimension property."""
        config = {"api_key": "test-key"}
        provider = GigaChatEmbeddingsProvider(config)
        assert provider.dimension == 1024


class TestYandexEmbeddingsProvider:
    """Tests for YandexEmbeddingsProvider."""
    
    def test_missing_credentials_raise_error(self):
        """Test that missing credentials raise ValueError."""
        with pytest.raises(ValueError, match="YANDEX_EMBEDDINGS_KEY not set"):
            YandexEmbeddingsProvider({"folder_id": "test"})
        
        with pytest.raises(ValueError, match="YANDEX_FOLDER_ID not set"):
            YandexEmbeddingsProvider({"api_key": "test"})
    
    @pytest.mark.asyncio
    @patch('telegram_rag_bot.embeddings.yandex.httpx.AsyncClient')
    async def test_embed_documents(self, mock_client_class):
        """Test embedding documents via Yandex API."""
        config = {
            "api_key": "test-key",
            "folder_id": "test-folder"
        }
        
        # Mock API responses (Yandex API accepts 1 text at a time)
        mock_response1 = Mock()
        mock_response1.json.return_value = {"embedding": [0.1, 0.2]}
        mock_response1.raise_for_status = Mock()
        
        mock_response2 = Mock()
        mock_response2.json.return_value = {"embedding": [0.3, 0.4]}
        mock_response2.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.post.side_effect = [mock_response1, mock_response2]
        mock_client_class.return_value = mock_client
        
        provider = YandexEmbeddingsProvider(config)
        
        texts = ["text1", "text2"]
        result = await provider.embed_documents(texts)
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert mock_client.post.call_count == 2
    
    def test_dimension(self):
        """Test dimension property."""
        config = {"api_key": "test-key", "folder_id": "test"}
        provider = YandexEmbeddingsProvider(config)
        assert provider.dimension == 256


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

