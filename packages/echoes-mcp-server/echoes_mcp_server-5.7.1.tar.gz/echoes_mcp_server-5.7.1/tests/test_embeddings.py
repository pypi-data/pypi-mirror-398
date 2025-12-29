"""Tests for embeddings module."""

from unittest.mock import MagicMock, patch

import numpy as np


class TestEmbeddings:
    """Tests for embedding functions."""

    def test_embed_query_returns_vector(self):
        with patch("echoes_mcp.indexer.embeddings.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([0.1] * 768)
            mock_get_model.return_value = mock_model

            from echoes_mcp.indexer.embeddings import embed_query

            result = embed_query("test query")

            assert len(result) == 768
            mock_model.encode.assert_called_once()

    def test_embed_texts_returns_vectors(self):
        with patch("echoes_mcp.indexer.embeddings.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 768, [0.2] * 768])
            mock_get_model.return_value = mock_model

            from echoes_mcp.indexer.embeddings import embed_texts

            result = embed_texts(["text1", "text2"])

            assert len(result) == 2
            assert len(result[0]) == 768

    def test_embed_texts_empty_list(self):
        from echoes_mcp.indexer.embeddings import embed_texts

        result = embed_texts([])
        assert result == []

    def test_embed_texts_with_progress_callback(self):
        with patch("echoes_mcp.indexer.embeddings.get_embedding_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 768])
            mock_get_model.return_value = mock_model

            from echoes_mcp.indexer.embeddings import embed_texts

            callback_called = []

            def callback(completed, total):
                callback_called.append((completed, total))

            embed_texts(["text"], progress_callback=callback)

            assert len(callback_called) > 0
