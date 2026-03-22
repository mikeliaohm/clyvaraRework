"""Pluggable embedding interface.

Start with LocalEmbedder (BGE via sentence-transformers).
OpenAIEmbedder is a stub for future cloud-provider support.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Common interface every embedder must satisfy."""

    model_name: str
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one vector per input."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        ...


# ---------------------------------------------------------------------------
# Local embedder (sentence-transformers / BGE)
# ---------------------------------------------------------------------------

class LocalEmbedder:
    """Wraps a sentence-transformers model loaded on the local machine."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


# ---------------------------------------------------------------------------
# OpenAI embedder (stub — for future cloud use)
# ---------------------------------------------------------------------------

class OpenAIEmbedder:
    """Wraps OpenAI's embedding API. Requires OPENAI_API_KEY."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        from config import openai_client

        if openai_client is None:
            raise RuntimeError("OpenAI client not configured (missing OPENAI_API_KEY)")
        self._client = openai_client
        self.model_name = model_name
        # text-embedding-3-small produces 1536-dim vectors by default
        self.dimension = 1536

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def get_embedder(model_name: str | None = None) -> Embedder:
    """Return an Embedder instance for the given model name.

    Recognised prefixes / names:
      - "text-embedding-*"  → OpenAIEmbedder
      - anything else        → LocalEmbedder (sentence-transformers)
    """
    name = model_name or _DEFAULT_MODEL

    if name.startswith("text-embedding-"):
        return OpenAIEmbedder(model_name=name)
    return LocalEmbedder(model_name=name)
