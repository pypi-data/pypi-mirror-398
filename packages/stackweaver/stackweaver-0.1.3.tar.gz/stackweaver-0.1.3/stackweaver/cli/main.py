"""
StackWeaver CLI - Main entry point for user commands.
"""

import difflib
import sys

import click

from stackweaver import __version__
from stackweaver.cli.ui_helpers import EMOJI, console, show_banner


class StackWeaverGroup(click.Group):
    """Custom Click Group with command suggestions."""

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        """Resolve command and provide suggestions for typos."""
        try:
            result: tuple[str | None, click.Command | None, list[str]] = super().resolve_command(
                ctx, args
            )
            return result
        except click.exceptions.UsageError:
            # Get available commands
            available_commands = list(self.list_commands(ctx))

            # Try to find similar commands
            if args:
                suggestions = difflib.get_close_matches(
                    args[0], available_commands, n=3, cutoff=0.5
                )

            if suggestions:
                console.print(f"\n[red]{EMOJI['error']} Unknown command:[/red] '{args[0]}'")
                console.print(f"\n[yellow]{EMOJI['info']} Did you mean one of these?[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • [cyan]{suggestion}[/cyan]")
                console.print(
                    "\n[dim]💡 Tip: Run [green]stackweaver --help[/green] to see all available commands.[/dim]\n"
                )
                sys.exit(1)

            # Re-raise if no suggestions
            raise


@click.group(cls=StackWeaverGroup)
@click.version_option(version=__version__, prog_name="stackweaver")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    StackWeaver - Orchestrate production-ready OSS tools via natural language.

    \b
    Example:
        stackweaver init "CRM with project management"    # Generate stack
        stackweaver deploy                                 # Deploy to Docker
        stackweaver status                                 # Check services
        stackweaver rollback                               # Undo deployment
    """
    # Show banner only for help or when no command is provided
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print(
            f"\n[yellow]{EMOJI['info']} Run 'stackweaver --help' for usage information.[/yellow]\n"
        )


@cli.command()
@click.argument("query", required=False)
@click.option(
    "--output",
    "-o",
    default="./stackweaver-stack",
    help="Output directory for generated files",
)
def init(query: str | None, output: str) -> None:
    """
    Initialize a new project with AI-powered tool selection.

    \b
    Example:
        stackweaver init "CRM with project management"
        stackweaver init "E-commerce + payments + analytics" -o ./my-shop
        stackweaver init  # Interactive mode
    """
    from stackweaver.cli.commands import init_command

    show_banner(title=f"{EMOJI['init']} StackWeaver Init", subtitle="AI-powered stack generation")

    # If no query provided, prompt for it
    if not query:
        console.print(
            f"\n[cyan]{EMOJI['sparkles']} Describe your project needs[/cyan] "
            "(e.g., 'CRM with email automation'):"
        )
        query = click.prompt("", type=str)

    # Type check: query is guaranteed to be str here
    assert query is not None, "Query should not be None after prompt"

    # Run init command
    init_command(query=query, output_dir=output)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Preview deployment without executing")
@click.option(
    "--stack-dir",
    "-d",
    default="./stackweaver-stack",
    help="Directory containing docker-compose.yml",
)
@click.option(
    "--project-name",
    "-p",
    default=None,
    help="Docker Compose project name (defaults to directory name)",
)
def deploy(dry_run: bool, stack_dir: str, project_name: str | None) -> None:
    """
    Deploy stack with Docker Compose.

    \b
    Example:
        stackweaver deploy                    # Deploy current stack
        stackweaver deploy -d ./my-stack      # Deploy specific stack
        stackweaver deploy --dry-run          # Preview without deploying
    """
    from stackweaver.cli.commands import deploy_command

    if dry_run:
        show_banner(
            title=f"{EMOJI['search']} Dry-Run Mode", subtitle="Preview deployment (no changes)"
        )
    else:
        show_banner(title=f"{EMOJI['deploy']} StackWeaver Deploy", subtitle="Deploying to Docker")

    # Run deploy command
    deploy_command(stack_dir=stack_dir, project_name=project_name, dry_run=dry_run)


@cli.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results to return")
@click.option("--no-llm", is_flag=True, help="Disable LLM re-ranking (faster)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed search metadata")
def search(query: str, top_k: int, no_llm: bool, verbose: bool) -> None:
    """
    Search for tools in the knowledge base.

    \b
    Example:
        stackweaver search "project management"           # Find tools
        stackweaver search "CRM with email" --top-k 10    # More results
        stackweaver search "analytics" --no-llm           # Skip AI ranking
    """
    from stackweaver.cli.commands import search_command

    search_command(query=query, top_k=top_k, use_llm=not no_llm, verbose=verbose)


@cli.command()
@click.option(
    "-d",
    "--stack-dir",
    default="./stackweaver-stack",
    help="Directory containing docker-compose.yml",
)
@click.option(
    "-p",
    "--project-name",
    default=None,
    help="Docker Compose project name",
)
def status(stack_dir: str, project_name: str | None) -> None:
    """
    Check the status of deployed services.

    \b
    Example:
        stackweaver status                # Check current stack
        stackweaver status -d ./my-stack  # Check specific stack
        stackweaver status -p myproject   # Check by project name
    """
    from stackweaver.cli.commands import status_command

    status_command(stack_dir=stack_dir, project_name=project_name)


@cli.command()
@click.option(
    "-d",
    "--stack-dir",
    default="./stackweaver-stack",
    help="Directory containing docker-compose.yml",
)
@click.option(
    "-p",
    "--project-name",
    default=None,
    help="Docker Compose project name",
)
@click.option(
    "-s",
    "--service",
    default=None,
    help="Show logs for specific service only",
)
@click.option(
    "-f",
    "--follow",
    is_flag=True,
    help="Follow log output (like tail -f)",
)
@click.option(
    "--tail",
    default=100,
    help="Number of lines to show from end",
)
def logs(
    stack_dir: str,
    project_name: str | None,
    service: str | None,
    follow: bool,
    tail: int,
) -> None:
    """
    Show logs for deployed services.

    \b
    Example:
        stackweaver logs                     # Show all logs
        stackweaver logs --follow            # Stream logs live
        stackweaver logs --service grafana   # Specific service
        stackweaver logs --tail 50           # Last 50 lines
    """
    from stackweaver.cli.commands import logs_command

    logs_command(
        stack_dir=stack_dir,
        project_name=project_name,
        service=service,
        follow=follow,
        tail=tail,
    )


@cli.command()
@click.option(
    "-d",
    "--stack-dir",
    default="./stackweaver-stack",
    help="Directory containing docker-compose.yml",
)
@click.option(
    "-p",
    "--project-name",
    default=None,
    help="Docker Compose project name",
)
def stop(stack_dir: str, project_name: str | None) -> None:
    """
    Stop running containers (preserves data).

    \b
    Example:
        stackweaver stop                # Stop current stack
        stackweaver stop -d ./my-stack  # Stop specific stack
        stackweaver stop -p myproject   # Stop by project name
    """
    from stackweaver.cli.commands import stop_command

    stop_command(stack_dir=stack_dir, project_name=project_name)


@cli.command()
@click.option(
    "-d",
    "--stack-dir",
    default="./stackweaver-stack",
    help="Directory containing docker-compose.yml",
)
@click.option(
    "-p",
    "--project-name",
    default=None,
    help="Docker Compose project name",
)
def start(stack_dir: str, project_name: str | None) -> None:
    """
    Start stopped containers.

    \b
    Example:
        stackweaver start                # Start current stack
        stackweaver start -d ./my-stack  # Start specific stack
        stackweaver start -p myproject   # Start by project name
    """
    from stackweaver.cli.commands import start_command

    start_command(stack_dir=stack_dir, project_name=project_name)


@cli.command()
@click.option(
    "-d",
    "--directory",
    default="./stackweaver-stack",
    help="Directory containing the stack.",
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option(
    "-p",
    "--project-name",
    default=None,
    help="Override the Docker Compose project name.",
    type=str,
)
@click.option(
    "--clean",
    is_flag=True,
    help="Also remove volumes (WARNING: DELETES ALL DATA).",
)
def rollback(directory: str, project_name: str | None, clean: bool) -> None:
    """
    Rollback a deployment by stopping containers.

    \b
    Example:
        stackweaver rollback              # Stop containers (keep data)
        stackweaver rollback --clean      # Stop + delete ALL data (WARNING)
        stackweaver rollback -d ./my-stack
    """
    from stackweaver.cli.commands import rollback_command

    show_banner(title=f"{EMOJI['rollback']} StackWeaver Rollback", subtitle="Reverting deployment")

    rollback_command(stack_dir=directory, project_name=project_name, clean=clean)


@cli.command()
def version() -> None:
    """
    Show StackWeaver version and system info.
    """
    import platform

    from rich.panel import Panel
    from rich.text import Text

    show_banner()

    info = Text()
    info.append(f"{EMOJI['sparkles']} Version: ", style="bold")
    info.append("0.1.0", style="bold green")
    info.append(" (Beta)\n", style="dim")

    info.append(f"{EMOJI['success']} Status: ", style="bold")
    info.append("Phase 1 Complete", style="green")
    info.append(" - Production Ready\n", style="dim")

    info.append(f"{EMOJI['tool']} Python: ", style="bold")
    info.append(f"{sys.version.split()[0]}\n", style="cyan")

    info.append(f"{EMOJI['docker']} Platform: ", style="bold")
    info.append(f"{platform.system()} {platform.machine()}\n", style="cyan")

    console.print("\n")
    console.print(Panel(info, title="System Info", border_style="green"))

    console.print(f"\n[bold green]{EMOJI['success']} Phase 1 Complete:[/bold green]")
    console.print(f"  {EMOJI['check']} Knowledge Base (55 OSS tools)")
    console.print(f"  {EMOJI['check']} AI-Powered Search & Ranking")
    console.print(f"  {EMOJI['check']} Stack Generation (Docker Compose + Traefik)")
    console.print(f"  {EMOJI['check']} Full Deployment Lifecycle")
    console.print(f"  {EMOJI['check']} CLI (9 commands)")
    console.print(f"  {EMOJI['check']} CI/CD Pipeline")
    console.print(f"  {EMOJI['check']} Comprehensive Testing")

    console.print(f"\n[bold cyan]{EMOJI['info']} What's Next:[/bold cyan]")
    console.print("  * Phase 2: Agentic Intelligence (Q1-Q3 2026)")
    console.print("  * LangGraph Integration")
    console.print("  * Interactive Conversations")
    console.print("  * Auto-Configuration")

    console.print(
        '\n[dim]Tip: Get started with [cyan]stackweaver init "your project idea"[/cyan][/dim]'
    )
    console.print("[dim]Docs: [cyan]https://github.com/stackweaver-io/stackweaver[/cyan][/dim]\n")


# Add secrets management commands
from stackweaver.cli.commands.secrets import secrets  # noqa: E402

cli.add_command(secrets)


if __name__ == "__main__":
    cli()
