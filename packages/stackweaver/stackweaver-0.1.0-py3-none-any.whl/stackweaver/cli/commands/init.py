"""
Init command implementation for StackWeaver CLI.

Handles natural language project initialization with tool search,
recommendation, and stack generation.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from stackweaver.cli.ui_helpers import (
    EMOJI,
    console,
    create_multi_task_progress,
    show_phase,
    show_step_success,
    show_task_list,
    with_spinner,
)
from stackweaver.generator.yaml_generator import YAMLGenerator
from stackweaver.search.llm_ranker import LLMRanker, LLMRankerConfig
from stackweaver.search.schemas import EnvVarSchema, ToolSchema, VolumeSchema
from stackweaver.search.tool_search import ToolSearch
from stackweaver.search.vector_store import VectorStore


def _convert_metadata_to_tool(metadata: dict[str, Any]) -> ToolSchema:
    """
    Convert ChromaDB metadata to ToolSchema.

    Handles type conversions for all fields.
    """
    # Parse JSON fields
    env_vars_raw = metadata.get("env_vars", "[]")
    env_vars = json.loads(env_vars_raw) if isinstance(env_vars_raw, str) else []
    env_vars_schemas = [EnvVarSchema(**ev) for ev in env_vars]

    volumes_raw = metadata.get("volumes", "[]")
    volumes = json.loads(volumes_raw) if isinstance(volumes_raw, str) else []
    volumes_schemas = [VolumeSchema(**v) for v in volumes]

    ports_raw = metadata.get("ports", "[]")
    ports = json.loads(ports_raw) if isinstance(ports_raw, str) else []

    dependencies_raw = metadata.get("dependencies", "[]")
    dependencies = json.loads(dependencies_raw) if isinstance(dependencies_raw, str) else []

    tags_raw = metadata.get("tags", "[]")
    tags = json.loads(tags_raw) if isinstance(tags_raw, str) else []

    # Parse datetime
    last_updated_raw = metadata.get("last_updated", "")
    if isinstance(last_updated_raw, str):
        last_updated = datetime.fromisoformat(last_updated_raw)
    else:
        last_updated = datetime.now()

    return ToolSchema(
        id=str(metadata.get("id", "")),
        name=str(metadata.get("name", "")),
        category=str(metadata.get("category", "")),
        docker_image=str(metadata.get("docker_image", "")),
        description=str(metadata.get("description", "")),
        github_stars=int(metadata.get("github_stars", 0)),
        last_updated=last_updated,
        security_score=float(metadata.get("security_score", 0.0)),
        stability_score=float(metadata.get("stability_score", 0.0)),
        env_vars=env_vars_schemas,
        volumes=volumes_schemas,
        ports=ports,
        dependencies=dependencies,
        tags=tags,
    )


def init_command(query: str, output_dir: str = "./stackweaver-stack") -> None:
    """
    Initialize a new StackWeaver project.

    Args:
        query: Natural language description of project needs
        output_dir: Directory to save generated files
    """
    start_time = time.time()

    # Show banner
    console.print("\n")
    console.print(
        Panel(
            "[bold cyan]StackWeaver Init[/bold cyan]\n"
            "Finding the perfect OSS tools for your project...",
            border_style="cyan",
        )
    )

    # Phase 1: Search & Analysis
    show_phase(1, 3, "Search & Analysis")

    # Show initial task list
    show_task_list(
        [
            ("Search knowledge base", "running"),
            ("Rank tools with AI", "pending"),
            ("Generate stack", "pending"),
        ]
    )

    # Step 1: Search for tools
    try:
        # Initialize search components
        with with_spinner("Initializing search engine", "Search engine ready!"):
            vector_store = VectorStore()

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
            searcher = ToolSearch(vector_store=vector_store, llm_ranker=llm_ranker)

        # Search for tools with progress
        with with_spinner(f"Searching for '{query}'", "Search complete!"):
            tool_results, search_metadata = searcher.find_tools(
                query, top_k=10, use_llm_rerank=True
            )

        if not tool_results:
            console.print(
                "\n[yellow]" + EMOJI["warning"] + "[/yellow] No tools found matching your query."
            )
            console.print("[dim]Try rephrasing your needs or being more specific.[/dim]")
            return

        # Get collection to fetch full tool metadata
        collection = vector_store.get_or_create_collection()

        # Convert ToolSearchResult to expected format
        results = []
        for result in tool_results:
            # Query ChromaDB for full metadata using tool_id
            tool_data = collection.get(ids=[result.tool_id], include=["metadatas"])
            if tool_data and tool_data["metadatas"]:
                metadata = tool_data["metadatas"][0]
                try:
                    tool = _convert_metadata_to_tool(dict(metadata))
                    results.append(
                        {
                            "tool": tool,
                            "score": result.quality_score,
                            "vector_time_ms": search_metadata.get("vector_time_ms", 0),
                            "llm_time_ms": search_metadata.get("llm_time_ms", 0),
                        }
                    )
                except Exception:
                    # Skip invalid tools
                    continue

        if not results:
            console.print(
                "\n[yellow]"
                + EMOJI["warning"]
                + "[/yellow] No valid tools found matching your query."
            )
            console.print("[dim]Try rephrasing your needs or being more specific.[/dim]")
            return

        # Update task list
        show_task_list(
            [
                ("Search knowledge base", "done"),
                ("Rank tools with AI", "done"),
                ("Generate stack", "pending"),
            ]
        )

    except Exception as e:
        console.print(f"\n[red]{EMOJI['cross']}[/red] Search failed: {e}")
        console.print(
            "[dim]Tip: Make sure you've run 'stackweaver ingest' to populate the knowledge base.[/dim]"
        )
        return

    # Phase 2: Tool Selection
    show_phase(2, 3, "Tool Selection")

    # Step 2: Display recommendations
    with with_spinner("Analyzing results", "Analysis complete!"):
        table = create_recommendations_table(results)

    console.print("\n")
    console.print(table)

    # Step 3: Confirm selection
    console.print("\n")
    if not Confirm.ask("[bold]Include these tools in your stack?[/bold]", default=True):
        console.print("\n[yellow]Cancelled.[/yellow] No files were generated.")
        return

    # Phase 3: Stack Generation
    show_phase(3, 3, "Stack Generation")

    # Step 4: Generate YAML and .env
    try:
        # Extract tools from results
        tools = [result["tool"] for result in results]

        # Generate with multi-task progress
        progress, tasks = create_multi_task_progress()
        with progress:
            # Task 1: Create directory
            tasks["dir"] = progress.add_task("[cyan]Creating output directory...", total=100)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            progress.update(tasks["dir"], completed=100)

            # Task 2: Generate docker-compose.yml
            tasks["yaml"] = progress.add_task("[cyan]Generating docker-compose.yml...", total=100)
            generator = YAMLGenerator()
            yaml_content = generator.generate(
                tools=tools,
                project_name=Path(output_dir).name,
                traefik_enabled=True,
                traefik_domain="localhost",
                https_enabled=False,
            )
            progress.update(tasks["yaml"], completed=100)

            # Task 3: Write docker-compose.yml
            tasks["write_yaml"] = progress.add_task(
                "[cyan]Writing docker-compose.yml...", total=100
            )
            compose_file = output_path / "docker-compose.yml"
            compose_file.write_text(yaml_content, encoding="utf-8")
            progress.update(tasks["write_yaml"], completed=100)

            # Task 4: Generate .env
            tasks["env"] = progress.add_task("[cyan]Generating .env file...", total=100)
            env_content = generator.generate_env(tools)
            progress.update(tasks["env"], completed=100)

            # Task 5: Write .env
            tasks["write_env"] = progress.add_task("[cyan]Writing .env file...", total=100)
            env_file = output_path / ".env"
            env_file.write_text(env_content, encoding="utf-8")
            progress.update(tasks["write_env"], completed=100)

        # Calculate total time
        total_time = time.time() - start_time

        # Success message
        show_step_success(f"Stack ready in {total_time:.2f}s!")
        console.print("\n")
        success_panel = Panel(
            f"[bold green]Generated successfully![/bold green]\n\n"
            f"Files created:\n"
            f"  {EMOJI['success']} {compose_file}\n"
            f"  {EMOJI['success']} {env_file}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. Review and customize .env file\n"
            f"  2. Run: [cyan]cd {output_dir}[/cyan]\n"
            f"  3. Run: [cyan]docker compose up -d[/cyan]",
            title="Success",
            border_style="green",
        )
        console.print(success_panel)
        console.print("\n")

    except Exception:
        console.print("\n[red]" + EMOJI["cross"] + "[/red] Generation failed: {e}")
        console.print("[dim]Check the error message above and try again.[/dim]")
        return


def create_recommendations_table(results: list[dict[str, Any]]) -> Table:
    """
    Create a Rich table displaying tool recommendations.

    Args:
        results: List of search results with tools and scores

    Returns:
        Rich Table object
    """
    table = Table(
        title="[bold cyan]Recommended Tools[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
    )

    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Description", style="dim")

    for result in results:
        tool = result["tool"]
        score = result.get("score", 0.0)

        # Format score as percentage
        score_str = f"{score*10:.1f}/10"

        # Truncate description if too long
        description = tool.description
        if len(description) > 50:
            description = description[:47] + "..."

        table.add_row(
            tool.name,
            tool.category,
            score_str,
            description,
        )

    return table
