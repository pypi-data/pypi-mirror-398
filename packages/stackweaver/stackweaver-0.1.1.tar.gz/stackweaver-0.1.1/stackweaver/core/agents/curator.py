"""
Curator Agent Interface for StackWeaver.

The Curator is responsible for tool search and recommendation based on
user queries. This interface enables Phase 2 migration to LangGraph agents
while maintaining backward compatibility with the current implementation.

Phase 1: SimpleCurator wraps VectorStore + LLM search
Phase 2: LangGraphCurator will use agentic reasoning with tool use
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from stackweaver.search.llm_ranker import LLMRanker
from stackweaver.search.tool_search import ToolSearch, ToolSearchResult
from stackweaver.search.vector_store import VectorStore

logger = logging.getLogger(__name__)


class CuratorAgent(ABC):
    """
    Abstract interface for tool curation and recommendation.

    The Curator agent is responsible for:
    - Understanding user needs from natural language
    - Searching tool catalog for matching tools
    - Ranking and filtering results by relevance
    - Providing recommendations with explanations

    Implementations:
    - SimpleCurator: Direct vector search + LLM ranking (Phase 1)
    - LangGraphCurator: Agentic reasoning with tools (Phase 2)
    """

    @abstractmethod
    def recommend_tools(
        self,
        user_query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> tuple[list[ToolSearchResult], dict[str, Any]]:
        """
        Recommend tools based on user query.

        Args:
            user_query: Natural language description of needs
            top_k: Maximum number of tools to recommend
            **kwargs: Additional parameters for specific implementations

        Returns:
            Tuple of (tool_results, metadata) where:
            - tool_results: List of recommended ToolSearchResult objects
            - metadata: Dict with search stats (time, scores, etc.)

        Raises:
            Exception: If search/recommendation fails
        """
        pass

    @abstractmethod
    def explain_recommendation(
        self,
        tool_result: ToolSearchResult,
        user_query: str,
    ) -> str:
        """
        Explain why a tool was recommended for the given query.

        Args:
            tool_result: The recommended tool
            user_query: Original user query

        Returns:
            Human-readable explanation of the recommendation

        Note:
            Phase 1: Simple template-based explanation
            Phase 2: LLM-generated contextual explanation
        """
        pass


class SimpleCurator(CuratorAgent):
    """
    Phase 1 implementation of CuratorAgent.

    Wraps existing ToolSearch functionality (VectorStore + LLM ranking)
    in the CuratorAgent interface. This provides a clean abstraction
    layer for Phase 2 migration to LangGraph.

    Example:
        >>> curator = SimpleCurator(vector_store, llm_ranker)
        >>> tools, metadata = curator.recommend_tools("I need a CRM")
        >>> print(f"Found {len(tools)} tools in {metadata['total_time_ms']}ms")
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_ranker: LLMRanker | None = None,
    ):
        """
        Initialize SimpleCurator with search components.

        Args:
            vector_store: ChromaDB vector store for semantic search
            llm_ranker: Optional LLM ranker for result re-ranking
        """
        self.vector_store = vector_store
        self.llm_ranker = llm_ranker
        self.tool_search = ToolSearch(vector_store, llm_ranker)
        logger.info("SimpleCurator initialized")

    def recommend_tools(
        self,
        user_query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> tuple[list[ToolSearchResult], dict[str, Any]]:
        """
        Recommend tools using vector search + optional LLM ranking.

        Args:
            user_query: Natural language description of needs
            top_k: Maximum number of tools to recommend
            **kwargs: Additional parameters:
                - use_llm_rerank: Whether to use LLM re-ranking (default: True if llm_ranker available)
                - filters: Optional filters for search

        Returns:
            Tuple of (tool_results, metadata)
        """
        use_llm_rerank = kwargs.get("use_llm_rerank", self.llm_ranker is not None)

        logger.info(f"Curator searching for: {user_query} (top_k={top_k})")

        tools, metadata = self.tool_search.find_tools(
            query=user_query,
            top_k=top_k,
            use_llm_rerank=use_llm_rerank,
        )

        logger.info(f"Curator found {len(tools)} tools in {metadata.get('total_time_ms', 0)}ms")

        return tools, metadata

    def explain_recommendation(
        self,
        tool_result: ToolSearchResult,
        user_query: str,
    ) -> str:
        """
        Provide a simple template-based explanation.

        Args:
            tool_result: The recommended tool
            user_query: Original user query

        Returns:
            Template-based explanation string

        Note:
            Phase 2 will use LLM to generate contextual explanations
        """
        # Calculate relevance (handle None distance)
        distance = tool_result.distance if tool_result.distance is not None else 0.0
        relevance = 1 - distance

        explanation = (
            f"{tool_result.name} is recommended because:\n"
            f"- Category: {tool_result.category}\n"
            f"- Quality Score: {tool_result.quality_score:.2f}\n"
            f"- Relevance: {relevance:.2%} match to your query\n"
            f"- Tags: {', '.join(tool_result.tags)}"
        )

        return explanation


# Phase 2 placeholder - will be implemented with LangGraph
class LangGraphCurator(CuratorAgent):
    """
    Phase 2 implementation using LangGraph agents.

    This will use agentic reasoning with:
    - Multi-step tool search and filtering
    - Context-aware recommendations
    - Interactive clarification questions
    - Explainable AI reasoning chains

    Example (Phase 2):
        >>> curator = LangGraphCurator(graph, tools)
        >>> tools, metadata = curator.recommend_tools("I need a CRM")
        >>> # Agent will reason about CRM requirements, ask clarifying questions
        >>> # and provide detailed explanations with reasoning chains
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Phase 2 implementation - not yet available."""
        raise NotImplementedError(
            "LangGraphCurator is planned for Phase 2. "
            "Use SimpleCurator for current functionality."
        )

    def recommend_tools(
        self,
        user_query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> tuple[list[ToolSearchResult], dict[str, Any]]:
        """Phase 2 implementation."""
        raise NotImplementedError("Phase 2 not yet implemented")

    def explain_recommendation(
        self,
        tool_result: ToolSearchResult,
        user_query: str,
    ) -> str:
        """Phase 2 implementation."""
        raise NotImplementedError("Phase 2 not yet implemented")
