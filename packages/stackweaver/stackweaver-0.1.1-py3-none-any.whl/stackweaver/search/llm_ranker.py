"""
LLM-based tool re-ranking for StackWeaver.

Uses LiteLLM to support multiple LLM providers (OpenAI, Anthropic, Ollama)
for intelligent tool selection and ranking.
"""

import logging
import os
from typing import Any

import litellm
from litellm import completion

logger = logging.getLogger(__name__)

# Set LiteLLM logging to WARNING to reduce noise
litellm.set_verbose = False


class LLMRankerConfig:
    """Configuration for LLM-based re-ranking."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        api_base: str | None = None,
        timeout: int = 5,
        temperature: float = 0.0,
    ) -> None:
        """
        Initialize LLM ranker configuration.

        Args:
            model: LLM model identifier (e.g., "gpt-4o", "ollama/llama3")
            api_key: API key for cloud providers (not needed for Ollama)
            api_base: Custom API base URL (e.g., for Ollama: "http://localhost:11434")
            timeout: Request timeout in seconds (default: 5)
            temperature: Sampling temperature (default: 0.0 for deterministic)
        """
        self.model = model

        # Auto-detect API key from environment if not provided
        if api_key is None:
            # Try STACKWEAVER_LLM_API_KEY first
            api_key = os.getenv("STACKWEAVER_LLM_API_KEY")
            # Fall back to standard provider keys
            if api_key is None:
                if "gpt" in model or "openai" in model.lower():
                    api_key = os.getenv("OPENAI_API_KEY")
                elif "claude" in model or "anthropic" in model.lower():
                    api_key = os.getenv("ANTHROPIC_API_KEY")

        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.temperature = temperature

    def is_ollama(self) -> bool:
        """Check if model is Ollama-based."""
        return self.model.startswith("ollama/")

    def requires_api_key(self) -> bool:
        """Check if model requires API key."""
        # Ollama and local models don't need API keys
        return not self.is_ollama()


class LLMRanker:
    """
    LLM-based tool re-ranking using LiteLLM.

    Supports multiple providers:
    - OpenAI (gpt-4o, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-5-sonnet, etc.)
    - Ollama (ollama/llama3, ollama/mistral, etc.)
    """

    def __init__(self, config: LLMRankerConfig) -> None:
        """
        Initialize LLM ranker.

        Args:
            config: LLMRankerConfig instance

        Raises:
            ValueError: If API key is missing for cloud providers
        """
        self.config = config

        # Validate configuration
        if config.requires_api_key() and not config.api_key:
            raise ValueError(
                f"API key required for model '{config.model}'. "
                f"Set llm_api_key in config or use Ollama."
            )

        logger.info(f"LLM Ranker initialized with model: {config.model}")

    def rerank_tools(
        self,
        user_query: str,
        tools: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Re-rank tools using LLM reasoning.

        Args:
            user_query: User's natural language query
            tools: List of tool metadata dicts from vector search
            top_k: Number of tools to return

        Returns:
            Re-ranked list of tools (best matches first)

        Raises:
            TimeoutError: If LLM request times out
            Exception: If LLM request fails
        """
        if not tools:
            return []

        # Construct prompt for LLM
        prompt = self._build_rerank_prompt(user_query, tools)

        try:
            # Call LLM via LiteLLM
            response = completion(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at selecting the best tools for user needs.",
                    },
                    {"role": "user", "content": prompt},
                ],
                api_key=self.config.api_key,
                api_base=self.config.api_base,
                timeout=self.config.timeout,
                temperature=self.config.temperature,
            )

            # Extract ranked tool IDs from response
            ranked_ids = self._parse_llm_response(response)

            # Reorder tools based on LLM ranking
            reranked = self._apply_ranking(tools, ranked_ids, top_k)

            logger.info(
                f"LLM re-ranked {len(tools)} tools to {len(reranked)} for query: {user_query[:50]}..."
            )

            return reranked

        except Exception as e:
            logger.warning(f"LLM re-ranking failed: {e}. Falling back to vector scores.")
            # Fallback: return top_k tools by vector score (original order)
            return tools[:top_k]

    def _build_rerank_prompt(self, user_query: str, tools: list[dict[str, Any]]) -> str:
        """
        Build prompt for LLM re-ranking.

        Args:
            user_query: User's query
            tools: Tool metadata dicts

        Returns:
            Formatted prompt string
        """
        tools_text = "\n\n".join(
            [
                f"Tool ID: {tool.get('id', 'unknown')}\n"
                f"Name: {tool.get('name', 'Unknown')}\n"
                f"Category: {tool.get('category', 'Unknown')}\n"
                f"Description: {tool.get('description', 'No description')}\n"
                f"Tags: {', '.join(tool.get('tags', []))}"
                for tool in tools
            ]
        )

        prompt = f"""User Query: "{user_query}"

Available Tools:
{tools_text}

Task: Rank these tools from most to least relevant for the user's query.
Consider:
1. Semantic match with query intent
2. Tool category and purpose
3. Tags and metadata

Output Format: Return ONLY the tool IDs in ranked order (best first), one per line.
Example:
tool-1
tool-3
tool-2

Your ranking:"""

        return prompt

    def _parse_llm_response(self, response: Any) -> list[str]:
        """
        Parse LLM response to extract ranked tool IDs.

        Args:
            response: LiteLLM completion response

        Returns:
            List of tool IDs in ranked order
        """
        try:
            # Extract text from LiteLLM response
            text = response.choices[0].message.content.strip()

            # Parse tool IDs (one per line)
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            # Filter out non-ID lines (explanations, etc.)
            tool_ids = [line for line in lines if not line.startswith("#")]

            return tool_ids

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _apply_ranking(
        self,
        tools: list[dict[str, Any]],
        ranked_ids: list[str],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Apply LLM ranking to original tools list.

        Args:
            tools: Original tools list
            ranked_ids: Tool IDs in ranked order
            top_k: Number of tools to return

        Returns:
            Re-ranked tools list
        """
        # Create tool lookup by ID
        tool_map = {tool.get("id"): tool for tool in tools}

        # Build re-ranked list
        reranked = []
        for tool_id in ranked_ids:
            if tool_id in tool_map:
                reranked.append(tool_map[tool_id])
                if len(reranked) >= top_k:
                    break

        # If LLM didn't rank all tools, append remaining ones
        ranked_set = set(ranked_ids)
        for tool in tools:
            if tool.get("id") not in ranked_set and len(reranked) < top_k:
                reranked.append(tool)

        return reranked[:top_k]

    def health_check(self) -> dict[str, Any]:
        """
        Verify LLM connectivity.

        Returns:
            Health status dict
        """
        try:
            # Simple test prompt
            response = completion(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello, respond with OK."}],
                api_key=self.config.api_key,
                api_base=self.config.api_base,
                timeout=self.config.timeout,
                max_tokens=10,
            )

            return {
                "status": "healthy",
                "model": self.config.model,
                "response": response.choices[0].message.content,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.config.model,
                "error": str(e),
            }
