"""
ChromaDB vector store for StackWeaver tool embeddings.

Provides persistent vector storage with semantic search capabilities.
"""

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB wrapper for StackWeaver tool catalog.

    Stores tool embeddings with metadata for semantic search and filtering.
    Uses local disk persistence for fast queries (<500ms) and data durability.
    """

    def __init__(self, persist_directory: Path | None = None) -> None:
        """
        Initialize ChromaDB with local disk persistence.

        Args:
            persist_directory: Path to ChromaDB storage.
                              Defaults to ~/.stackweaver/chroma_db/

        Raises:
            PermissionError: If directory is not writable
            OSError: If directory creation fails
        """
        if persist_directory is None:
            persist_directory = Path.home() / ".stackweaver" / "chroma_db"

        # Ensure directory exists with proper permissions
        try:
            persist_directory.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create ChromaDB directory at {persist_directory}. "
                f"Check file permissions."
            ) from e
        except OSError as e:
            raise OSError(f"Failed to create ChromaDB directory at {persist_directory}: {e}") from e

        # Verify directory is writable
        if not persist_directory.exists() or not persist_directory.is_dir():
            raise OSError(f"ChromaDB path {persist_directory} is not a valid directory")

        # Initialize ChromaDB client with persistence
        try:
            self.client: Any = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                ),
            )
            logger.info(f"ChromaDB initialized at {persist_directory}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB client: {e}") from e

        self.persist_directory = persist_directory

    def get_or_create_collection(
        self,
        name: str = "tools",
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        """
        Get existing collection or create if not exists.

        Args:
            name: Collection name (default: "tools")
            metadata: Collection metadata. Defaults to cosine similarity.

        Returns:
            ChromaDB Collection instance

        Raises:
            ValueError: If collection creation fails
        """
        if metadata is None:
            # Use cosine similarity for semantic search
            # HNSW (Hierarchical Navigable Small World) index for fast approximate search
            metadata = {"hnsw:space": "cosine"}

        try:
            collection: Collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata,
            )
            logger.info(f"Collection '{name}' ready (documents: {collection.count()})")
            return collection
        except Exception as e:
            raise ValueError(f"Failed to get/create collection '{name}': {e}") from e

    def reset_collection(self, name: str = "tools") -> Collection:
        """
        Delete and recreate collection (useful for testing/reindexing).

        Args:
            name: Collection name to reset

        Returns:
            New empty Collection instance
        """
        try:
            self.client.delete_collection(name=name)
            logger.warning(f"Collection '{name}' deleted")
        except (ValueError, Exception):
            # Collection doesn't exist, that's fine
            logger.debug(f"Collection '{name}' not found, creating new one")
            pass

        return self.get_or_create_collection(name=name)

    def health_check(self) -> dict[str, Any]:
        """
        Verify ChromaDB is operational.

        Returns:
            Health status dict with diagnostics
        """
        try:
            # Test database connectivity
            heartbeat = self.client.heartbeat()

            # Get collections count
            collections = self.client.list_collections()

            return {
                "status": "healthy",
                "heartbeat": heartbeat,
                "collections": len(collections),
                "persist_directory": str(self.persist_directory),
                "writable": self.persist_directory.exists() and self.persist_directory.is_dir(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "persist_directory": str(self.persist_directory),
            }

    def get_collection_stats(self, name: str = "tools") -> dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            name: Collection name

        Returns:
            Stats dict with count, metadata, etc.

        Raises:
            ValueError: If collection doesn't exist
        """
        try:
            collection = self.client.get_collection(name=name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except (ValueError, Exception) as e:
            raise ValueError(f"Collection '{name}' not found") from e
