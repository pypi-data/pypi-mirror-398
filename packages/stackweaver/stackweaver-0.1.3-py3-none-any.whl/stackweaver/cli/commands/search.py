"""
Search command implementation for StackWeaver CLI.

Handles semantic tool search with optional LLM re-ranking.
"""

import os
import time
from typing import Any

from stackweaver.cli.ui_helpers import (
    EMOJI,
    console,
    create_table,
    show_step,
    show_step_error,
    show_step_success,
    show_step_warning,
    show_tip,
)
from stackweaver.search.llm_ranker import LLMRanker, LLMRankerConfig
from stackweaver.search.tool_search import ToolSearch
from stackweaver.search.vector_store import VectorStore


def search_command(
    query: str,
    top_k: int = 5,
    use_llm: bool = True,
    verbose: bool = False,
) -> None:
    """
    Search for tools in the knowledge base.

    Args:
        query: Natural language search query
        top_k: Number of results to return
        use_llm: Whether to use LLM re-ranking
        verbose: Show detailed search metadata
    """
    start_time = time.time()

    # Show banner
    from rich.panel import Panel

    console.print("\n")
    console.print(
        Panel(
            f"[bold cyan]{EMOJI['search']} Tool Search[/bold cyan]\n"
            f"Query: [yellow]{query}[/yellow]",
            border_style="cyan",
        )
    )

    try:
        # Initialize search components
        show_step("Initializing search engine", EMOJI["loading"])
        vector_store = VectorStore()

        llm_ranker = None
        if use_llm:
            try:
                # Read LLM config from environment variables
                llm_model = os.getenv("STACKWEAVER_LLM_MODEL", "gpt-3.5-turbo")
                llm_api_base = os.getenv("STACKWEAVER_LLM_API_BASE")
                llm_timeout = int(os.getenv("STACKWEAVER_LLM_TIMEOUT", "30"))

                llm_config = LLMRankerConfig(
                    model=llm_model,
                    api_base=llm_api_base,
                    timeout=llm_timeout,
                )
                llm_ranker = LLMRanker(config=llm_config)
            except Exception as e:
                show_step_warning(f"LLM re-ranking unavailable: {e}")
                console.print("[dim]Falling back to vector search only.[/dim]")
                use_llm = False

        searcher = ToolSearch(vector_store=vector_store, llm_ranker=llm_ranker)

        # Perform search
        show_step(f"Searching for '{query}'", EMOJI["search"])
        tool_results, search_metadata = searcher.find_tools(
            query, top_k=top_k, use_llm_rerank=use_llm
        )

        search_time = time.time() - start_time

        if not tool_results:
            show_step_warning("No tools found matching your query")
            console.print("[dim]Try rephrasing your query or being more general.[/dim]\n")
            return

        # Display results
        show_step_success(f"Found {len(tool_results)} tools")
        if verbose:
            console.print(
                f"[dim]Vector search: {search_metadata.get('vector_time_ms', 0):.0f}ms[/dim]"
            )
            if use_llm:
                console.print(
                    f"[dim]LLM re-ranking: {search_metadata.get('llm_time_ms', 0):.0f}ms[/dim]"
                )
            console.print(f"[dim]Total time: {search_time:.2f}s[/dim]")

        # Create results table
        table = create_search_results_table(tool_results)
        console.print("\n")
        console.print(table)

        # Show tip
        show_tip(
            "Use [cyan]stackweaver init '<your query>'[/cyan] to generate a stack with these tools"
        )

    except Exception as e:
        show_step_error(f"Search failed: {e}")
        if "collection" in str(e).lower() or "not found" in str(e).lower():
            show_step_warning("Knowledge base not initialized")
            console.print("[dim]Run: [cyan]python -m stackweaver.search.ingest[/cyan][/dim]\n")
        else:
            console.print("[dim]Check the error message above and try again.[/dim]\n")


def create_search_results_table(results: list[Any]) -> object:
    """
    Create a Rich table displaying search results.

    Args:
        results: List of ToolSearchResult objects

    Returns:
        Rich Table object
    """
    columns: list[tuple[str, dict[str, Any]]] = [
        ("#", {"style": "dim", "width": 3, "justify": "right"}),
        ("Tool", {"style": "cyan", "no_wrap": True, "width": 20}),
        ("Category", {"style": "yellow", "width": 15}),
        ("Score", {"justify": "right", "style": "green", "width": 8}),
        ("Description", {"style": "dim"}),
    ]

    table = create_table(f"{EMOJI['search']} Search Results", columns, border_style="cyan")

    for idx, result in enumerate(results, 1):
        # Format score
        score = result.quality_score
        if score >= 0.9:
            score_style = "bold green"
        elif score >= 0.7:
            score_style = "green"
        elif score >= 0.5:
            score_style = "yellow"
        else:
            score_style = "red"

        score_str = f"[{score_style}]{score*10:.1f}/10[/{score_style}]"

        # Truncate description
        description = result.description
        if len(description) > 60:
            description = description[:57] + "..."

        table.add_row(
            str(idx),
            result.name,
            result.category,
            score_str,
            description,
        )

    return table
