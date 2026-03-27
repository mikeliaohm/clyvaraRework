"""Central model registry — import all models here so Alembic can discover them."""

from models.rag import RagDocument, RagNode, RagChunk, IngestionRun  # noqa: F401
