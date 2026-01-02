"""
Tool catalog ingestion script for StackWeaver.

Loads tools from tools_index.json, validates, and stores in ChromaDB with embeddings.
"""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn

from stackweaver.search.schemas import ToolSchema
from stackweaver.search.vector_store import VectorStore

logger = logging.getLogger(__name__)
console = Console()


class ToolIngestionError(Exception):
    """Raised when tool ingestion fails."""


def load_tools_catalog(catalog_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Load tools from tools_index.json.

    Args:
        catalog_path: Path to tools_index.json.
                     Defaults to stackweaver/knowledge_base/tools_index.json

    Returns:
        List of tool dictionaries

    Raises:
        FileNotFoundError: If catalog file doesn't exist
        json.JSONDecodeError: If catalog is invalid JSON
    """
    if catalog_path is None:
        # Default: stackweaver/knowledge_base/tools_index.json
        catalog_path = Path(__file__).parent.parent / "knowledge_base" / "tools_index.json"

    if not catalog_path.exists():
        raise FileNotFoundError(f"Tool catalog not found at {catalog_path}")

    try:
        with open(catalog_path, encoding="utf-8") as f:
            data: list[dict[str, Any]] = json.load(f)
            return data
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {catalog_path}: {e.msg}", e.doc, e.pos) from e


def validate_tools(tools_data: list[dict[str, Any]]) -> list[ToolSchema]:
    """
    Validate all tools against ToolSchema.

    Args:
        tools_data: Raw tool dictionaries from JSON

    Returns:
        List of validated ToolSchema instances

    Raises:
        ToolIngestionError: If any tool fails validation
    """
    validated_tools: list[ToolSchema] = []
    errors: list[str] = []

    for idx, tool_data in enumerate(tools_data):
        try:
            tool = ToolSchema(**tool_data)
            validated_tools.append(tool)
        except ValidationError as e:
            tool_id = tool_data.get("id", f"index-{idx}")
            error_msg = f"Tool '{tool_id}' validation failed: {e}"
            errors.append(error_msg)
            logger.error(error_msg)

    if errors:
        raise ToolIngestionError(
            f"Failed to validate {len(errors)} tools:\n" + "\n".join(errors[:5])
        )

    return validated_tools


def generate_document_text(tool: ToolSchema) -> str:
    """
    Generate searchable text for a tool.

    Combines name, description, category, and tags into a rich document
    for semantic search.

    Args:
        tool: Validated ToolSchema instance

    Returns:
        Searchable document text
    """
    # Combine multiple fields for rich semantic context
    parts = [
        f"Name: {tool.name}",
        f"Category: {tool.category}",
        f"Description: {tool.description}",
        f"Tags: {', '.join(tool.tags)}",
    ]

    return " | ".join(parts)


def _serialize_metadata(tool: ToolSchema) -> dict[str, Any]:
    """
    Serialize ToolSchema to ChromaDB-compatible metadata.

    ChromaDB only supports scalar metadata types (str, int, float, bool).
    Complex types (lists, dicts) must be JSON-serialized.

    Args:
        tool: ToolSchema instance

    Returns:
        Flattened metadata dict with JSON-serialized complex fields
    """
    metadata: dict[str, Any] = {
        "id": tool.id,
        "name": tool.name,
        "category": tool.category,
        "docker_image": tool.docker_image,
        "description": tool.description,
        "github_stars": tool.github_stars,
        "last_updated": tool.last_updated.isoformat(),
        "security_score": tool.security_score,
        "stability_score": tool.stability_score,
        "quality_score": tool.calculate_quality_score(),
        # Serialize lists/dicts to JSON strings
        "ports": json.dumps(tool.ports),
        "dependencies": json.dumps(tool.dependencies),
        "tags": json.dumps(tool.tags),
        "env_vars": json.dumps([v.model_dump() for v in tool.env_vars]),
        "volumes": json.dumps([v.model_dump() for v in tool.volumes]),
    }

    return metadata


def ingest_tools_to_chromadb(
    tools: list[ToolSchema],
    vector_store: VectorStore,
    collection_name: str = "tools",
    force_reset: bool = False,
) -> dict[str, Any]:
    """
    Ingest validated tools into ChromaDB.

    Args:
        tools: Validated ToolSchema instances
        vector_store: VectorStore instance
        collection_name: Collection name (default: "tools")
        force_reset: If True, clear collection before ingestion

    Returns:
        Ingestion statistics dict

    Raises:
        ToolIngestionError: If ingestion fails
    """
    try:
        # Get or create collection
        if force_reset:
            collection = vector_store.reset_collection(collection_name)
            console.print(f"[yellow]Collection '{collection_name}' reset[/yellow]")
        else:
            collection = vector_store.get_or_create_collection(collection_name)

        # Check existing tools for idempotency
        existing_ids = set()
        if collection.count() > 0:
            existing_data = collection.get()
            existing_ids = set(existing_data["ids"])

        # Prepare data for batch ingestion
        new_tools = [t for t in tools if t.id not in existing_ids]
        update_tools = [t for t in tools if t.id in existing_ids]

        if not new_tools and not update_tools:
            console.print("[green]All tools already ingested (idempotent)[/green]")
            return {
                "total": len(tools),
                "new": 0,
                "updated": 0,
                "skipped": len(tools),
                "errors": 0,
            }

        # Ingest new tools with progress bar
        stats = {"total": len(tools), "new": 0, "updated": 0, "skipped": 0, "errors": 0}

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Ingest new tools
            if new_tools:
                task: TaskID = progress.add_task(
                    "[cyan]Ingesting new tools...", total=len(new_tools)
                )

                for tool in new_tools:
                    try:
                        doc_text = generate_document_text(tool)
                        # Serialize metadata (ChromaDB only supports scalar types)
                        metadata = _serialize_metadata(tool)

                        collection.add(
                            ids=[tool.id],
                            documents=[doc_text],
                            metadatas=[metadata],
                        )
                        stats["new"] += 1
                        progress.update(task, advance=1, description=f"[cyan]Ingested: {tool.name}")
                    except Exception as e:
                        logger.error(f"Failed to ingest tool '{tool.id}': {e}")
                        stats["errors"] += 1
                        progress.update(task, advance=1)

            # Update existing tools
            if update_tools:
                task_update = progress.add_task(
                    "[yellow]Updating existing tools...", total=len(update_tools)
                )

                for tool in update_tools:
                    try:
                        # Delete old entry
                        collection.delete(ids=[tool.id])

                        # Add updated entry
                        doc_text = generate_document_text(tool)
                        metadata = _serialize_metadata(tool)

                        collection.add(
                            ids=[tool.id],
                            documents=[doc_text],
                            metadatas=[metadata],
                        )
                        stats["updated"] += 1
                        progress.update(
                            task_update,
                            advance=1,
                            description=f"[yellow]Updated: {tool.name}",
                        )
                    except Exception as e:
                        logger.error(f"Failed to update tool '{tool.id}': {e}")
                        stats["errors"] += 1
                        progress.update(task_update, advance=1)

        # Print summary
        console.print()
        if stats["errors"] == 0:
            console.print(
                f"[green]Successfully ingested {stats['new']} new tools, "
                f"updated {stats['updated']} existing tools[/green]"
            )
        else:
            console.print(
                f"[yellow]Warning: Ingested {stats['new']} new tools, "
                f"updated {stats['updated']} existing tools, "
                f"with {stats['errors']} errors[/yellow]"
            )

        return stats

    except Exception as e:
        raise ToolIngestionError(f"Ingestion failed: {e}") from e


def main(
    catalog_path: Path | None = None,
    persist_directory: Path | None = None,
    force_reset: bool = False,
) -> int:
    """
    Main ingestion script entry point.

    Args:
        catalog_path: Path to tools_index.json
        persist_directory: ChromaDB storage path
        force_reset: Clear collection before ingestion

    Returns:
        Exit code (0 = success, 1 = error)
    """
    console.print()
    console.print("[bold cyan]StackWeaver Tool Ingestion[/bold cyan]")
    console.print()

    try:
        # Load catalog
        console.print("[cyan]Loading tool catalog...[/cyan]")
        tools_data = load_tools_catalog(catalog_path)
        console.print(f"[green]   Loaded {len(tools_data)} tools[/green]")

        # Validate tools
        console.print("[cyan]Validating tools against schema...[/cyan]")
        tools = validate_tools(tools_data)
        console.print(f"[green]   All {len(tools)} tools validated[/green]")

        # Initialize vector store
        console.print("[cyan]Initializing ChromaDB...[/cyan]")
        vector_store = VectorStore(persist_directory=persist_directory)
        health = vector_store.health_check()
        if health["status"] == "healthy":
            console.print(f"[green]   ChromaDB ready at {health['persist_directory']}[/green]")
        else:
            console.print(f"[red]   ChromaDB unhealthy: {health['error']}[/red]")
            return 1

        # Ingest tools
        console.print("[cyan]Ingesting tools to ChromaDB...[/cyan]")
        console.print()
        stats = ingest_tools_to_chromadb(tools, vector_store, force_reset=force_reset)

        # Final summary
        console.print()
        console.print("[bold green]Ingestion Complete![/bold green]")
        console.print(f"   Total tools: {stats['total']}")
        console.print(f"   New: {stats['new']}")
        console.print(f"   Updated: {stats['updated']}")
        console.print(f"   Errors: {stats['errors']}")
        console.print()

        return 0 if stats["errors"] == 0 else 1

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON Error: {e}[/red]")
        return 1
    except ToolIngestionError as e:
        console.print(f"[red]Ingestion Error: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected Error: {e}[/red]")
        logger.exception("Unexpected error during ingestion")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = main()
    sys.exit(exit_code)
