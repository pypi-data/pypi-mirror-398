"""
Semantic tool search for StackWeaver.

Combines vector search (ChromaDB) with LLM re-ranking for intelligent tool discovery.
"""

import json
import logging
import time
from typing import Any

from stackweaver.search.llm_ranker import LLMRanker
from stackweaver.search.vector_store import VectorStore

logger = logging.getLogger(__name__)


class ToolSearchResult:
    """Result from a tool search query."""

    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        quality_score: float,
        category: str,
        docker_image: str,
        tags: list[str],
        distance: float | None = None,
    ) -> None:
        """
        Initialize search result.

        Args:
            tool_id: Tool identifier
            name: Tool name
            description: Tool description
            quality_score: Quality score (0-10)
            category: Tool category
            docker_image: Docker image name
            tags: Tool tags
            distance: Vector distance (lower = more similar)
        """
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.quality_score = quality_score
        self.category = category
        self.docker_image = docker_image
        self.tags = tags
        self.distance = distance

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "quality_score": round(self.quality_score, 2),
            "category": self.category,
            "docker_image": self.docker_image,
            "tags": self.tags,
            "distance": round(self.distance, 4) if self.distance else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ToolSearchResult: {self.name} "
            f"(quality={self.quality_score:.1f}, distance={self.distance:.4f if self.distance else 'N/A'})>"
        )


class ToolSearch:
    """
    Semantic tool search with vector + LLM hybrid ranking.

    Combines ChromaDB vector search for semantic similarity with optional
    LLM re-ranking for intent understanding.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_ranker: LLMRanker | None = None,
        collection_name: str = "tools",
    ) -> None:
        """
        Initialize tool search.

        Args:
            vector_store: VectorStore instance
            llm_ranker: Optional LLMRanker for re-ranking
            collection_name: ChromaDB collection name
        """
        self.vector_store = vector_store
        self.llm_ranker = llm_ranker
        self.collection_name = collection_name

        # Get collection
        try:
            self.collection = vector_store.get_or_create_collection(collection_name)
            logger.info(f"ToolSearch initialized with {self.collection.count()} tools")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ToolSearch: {e}") from e

    def find_tools(
        self,
        query: str,
        top_k: int = 3,
        use_llm_rerank: bool = True,
        vector_candidates: int = 10,
    ) -> tuple[list[ToolSearchResult], dict[str, Any]]:
        """
        Search for tools using semantic search.

        Args:
            query: Natural language search query
            top_k: Number of results to return (default: 3)
            use_llm_rerank: Whether to use LLM re-ranking (default: True)
            vector_candidates: Number of vector candidates to fetch (default: 10)

        Returns:
            Tuple of (results, metadata) where metadata includes timing info

        Raises:
            ValueError: If query is empty or invalid
        """
        start_time = time.time()

        # Validate query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        query = query.strip()

        # Metadata for timing and diagnostics
        metadata: dict[str, Any] = {
            "query": query,
            "vector_time_ms": 0,
            "llm_time_ms": 0,
            "total_time_ms": 0,
            "used_llm_rerank": False,
            "llm_fallback": False,
            "total_tools": self.collection.count(),
        }

        # Step 1: Vector search via ChromaDB
        vector_start = time.time()
        try:
            # Ensure n_results is at least 1
            n_results = max(1, min(vector_candidates, self.collection.count()))
            vector_results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise RuntimeError(f"Vector search failed: {e}") from e

        vector_time = (time.time() - vector_start) * 1000
        metadata["vector_time_ms"] = round(vector_time, 2)

        # Check if results found
        if not vector_results["ids"] or not vector_results["ids"][0]:
            logger.warning(f"No tools found for query: {query}")
            metadata["total_time_ms"] = round((time.time() - start_time) * 1000, 2)
            return [], metadata

        # Parse vector results
        candidates = self._parse_vector_results(dict(vector_results))

        # Step 2: Optional LLM re-ranking
        final_results = candidates
        if use_llm_rerank and self.llm_ranker:
            llm_start = time.time()
            try:
                reranked = self.llm_ranker.rerank_tools(query, candidates, top_k=top_k)
                final_results = reranked
                metadata["used_llm_rerank"] = True
            except Exception as e:
                logger.warning(f"LLM re-ranking failed, using vector results: {e}")
                metadata["llm_fallback"] = True
                final_results = candidates[:top_k]

            llm_time = (time.time() - llm_start) * 1000
            metadata["llm_time_ms"] = round(llm_time, 2)
        else:
            # No LLM: use top_k from vector search
            final_results = candidates[:top_k]

        # Convert to ToolSearchResult objects
        results = [
            self._dict_to_result(tool, idx) for idx, tool in enumerate(final_results[:top_k])
        ]

        # Calculate total time
        total_time = (time.time() - start_time) * 1000
        metadata["total_time_ms"] = round(total_time, 2)
        metadata["num_results"] = len(results)

        logger.info(
            f"Search complete: {len(results)} results in {total_time:.0f}ms "
            f"(vector: {vector_time:.0f}ms, llm: {metadata['llm_time_ms']:.0f}ms)"
        )

        return results, metadata

    def _parse_vector_results(self, vector_results: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Parse ChromaDB vector results into tool dicts.

        Args:
            vector_results: Raw ChromaDB query results

        Returns:
            List of tool metadata dicts
        """
        tools = []

        ids = vector_results["ids"][0]
        metadatas = vector_results["metadatas"][0] if vector_results["metadatas"] else []
        distances = vector_results["distances"][0] if vector_results["distances"] else []

        for idx, tool_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = distances[idx] if idx < len(distances) else None

            # Deserialize JSON fields
            tool = {
                "id": tool_id,
                "name": metadata.get("name", "Unknown"),
                "description": metadata.get("description", "No description"),
                "category": metadata.get("category", "Unknown"),
                "docker_image": metadata.get("docker_image", "unknown:latest"),
                "quality_score": metadata.get("quality_score", 0.0),
                "tags": json.loads(metadata.get("tags", "[]")),
                "distance": distance,
            }

            tools.append(tool)

        return tools

    def _dict_to_result(self, tool: dict[str, Any], rank: int) -> ToolSearchResult:
        """
        Convert tool dict to ToolSearchResult.

        Args:
            tool: Tool metadata dict
            rank: Result rank (0-indexed)

        Returns:
            ToolSearchResult instance
        """
        return ToolSearchResult(
            tool_id=tool["id"],
            name=tool["name"],
            description=tool["description"],
            quality_score=tool.get("quality_score", 0.0),
            category=tool["category"],
            docker_image=tool["docker_image"],
            tags=tool.get("tags", []),
            distance=tool.get("distance"),
        )

    def search_by_category(self, category: str, top_k: int = 10) -> list[ToolSearchResult]:
        """
        Search tools by category.

        Args:
            category: Tool category (e.g., "CRM", "Database")
            top_k: Number of results

        Returns:
            List of ToolSearchResult
        """
        try:
            # Query with category filter
            results = self.collection.get(
                where={"category": category},
                limit=top_k,
            )

            if not results["ids"]:
                return []

            # Convert to ToolSearchResult
            tools = []
            for idx, tool_id in enumerate(results["ids"]):
                metadata = results["metadatas"][idx] if results["metadatas"] else {}
                tags_raw = metadata.get("tags", "[]")
                tags = json.loads(tags_raw) if isinstance(tags_raw, str) else []
                tool = {
                    "id": tool_id,
                    "name": metadata.get("name", "Unknown"),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", category),
                    "docker_image": metadata.get("docker_image", ""),
                    "quality_score": metadata.get("quality_score", 0.0),
                    "tags": tags,
                    "distance": None,
                }
                tools.append(self._dict_to_result(tool, idx))

            return tools

        except Exception as e:
            logger.error(f"Category search failed for '{category}': {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """
        Get search statistics.

        Returns:
            Statistics dict
        """
        try:
            return {
                "total_tools": self.collection.count(),
                "collection_name": self.collection_name,
                "llm_enabled": self.llm_ranker is not None,
                "vector_store_health": self.vector_store.health_check(),
            }
        except Exception as e:
            return {"error": str(e)}
