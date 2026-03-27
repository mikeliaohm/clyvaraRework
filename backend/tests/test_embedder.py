"""Unit tests for rag.embedder — caching behavior."""

from unittest.mock import patch, MagicMock
import rag.embedder as embedder_module
from rag.embedder import get_embedder, _embedder_cache


def _clear_cache():
    """Clear the global embedder cache between tests."""
    _embedder_cache.clear()


# ── get_embedder caching ─────────────────────────────────────

def test_get_embedder_returns_same_instance():
    _clear_cache()

    with patch.object(embedder_module, "LocalEmbedder") as MockLocal:
        mock_instance = MagicMock()
        mock_instance.model_name = "test-model"
        MockLocal.return_value = mock_instance

        first = get_embedder("test-model")
        second = get_embedder("test-model")

        assert first is second
        MockLocal.assert_called_once()  # only created once

    _clear_cache()


def test_get_embedder_different_models_cached_separately():
    _clear_cache()

    with patch.object(embedder_module, "LocalEmbedder") as MockLocal:
        mock_a = MagicMock()
        mock_a.model_name = "model-a"
        mock_b = MagicMock()
        mock_b.model_name = "model-b"
        MockLocal.side_effect = [mock_a, mock_b]

        a = get_embedder("model-a")
        b = get_embedder("model-b")

        assert a is not b
        assert MockLocal.call_count == 2

    _clear_cache()


def test_get_embedder_openai_prefix_uses_openai_embedder():
    _clear_cache()

    with patch.object(embedder_module, "OpenAIEmbedder") as MockOpenAI:
        mock_instance = MagicMock()
        MockOpenAI.return_value = mock_instance

        result = get_embedder("text-embedding-3-small")

        MockOpenAI.assert_called_once_with(model_name="text-embedding-3-small")
        assert result is mock_instance

    _clear_cache()


def test_get_embedder_local_prefix_uses_local_embedder():
    _clear_cache()

    with patch.object(embedder_module, "LocalEmbedder") as MockLocal:
        mock_instance = MagicMock()
        MockLocal.return_value = mock_instance

        result = get_embedder("BAAI/bge-small-en-v1.5")

        MockLocal.assert_called_once_with(model_name="BAAI/bge-small-en-v1.5")
        assert result is mock_instance

    _clear_cache()


def test_get_embedder_uses_default_model():
    _clear_cache()

    with patch.object(embedder_module, "_DEFAULT_MODEL", "my-default-model"):
        with patch.object(embedder_module, "LocalEmbedder") as MockLocal:
            mock_instance = MagicMock()
            MockLocal.return_value = mock_instance

            result = get_embedder()  # no model_name specified

            MockLocal.assert_called_once_with(model_name="my-default-model")

    _clear_cache()
