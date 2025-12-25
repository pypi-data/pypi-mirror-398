from typing import Annotated

import typer

from .ai_commit import run_ai_commit
from .init import run_init
from .keys import (
    Provider,
    get_default_provider,
    get_key,
    list_keys,
    list_providers,
    lock,
    migrate_legacy_keys,
    remove_key,
    set_default_provider,
    set_key,
    unlock,
)
from .prompt import prompt_app
from .summarize import run_summarize

app = typer.Typer()
keys_app = typer.Typer()
ai_commit_app = typer.Typer()

app.add_typer(keys_app, name="keys", help="Key management commands")
app.add_typer(ai_commit_app, name="ai-commit", help="AI-powered commit messages")
app.add_typer(prompt_app, name="prompt", help="Prompt template management")


@app.command()
def init() -> None:
    typer.echo("Running `init`")
    run_init()


@app.command()
def summarize(
    path: Annotated[str, typer.Argument(help="File or directory to summarize")] = ".",
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-x", help="Glob patterns to exclude"),
    ] = None,
    depth: Annotated[
        int, typer.Option("--depth", help="Max recursion depth (-1 = unlimited)")
    ] = -1,
    force: Annotated[
        bool, typer.Option("--force", help="Regenerate even if up-to-date")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show actions without writing")
    ] = False,
    max_file_bytes: Annotated[
        int, typer.Option("--max-file-bytes", help="Read limit per file")
    ] = 120_000,
    quiet: Annotated[bool, typer.Option("--quiet", help="Reduce output")] = False,
    include_ignored: Annotated[
        bool, typer.Option("--include-ignored", help="Process gitignored files")
    ] = False,
) -> None:
    """Generate structured markdown summaries of files and directories."""
    try:
        run_summarize(
            target=path,
            excludes=exclude or [],
            depth=depth,
            force=force,
            dry_run=dry_run,
            max_file_bytes=max_file_bytes,
            quiet=quiet,
            include_ignored=include_ignored,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


# AI Commit commands


@ai_commit_app.command()
def install(
    titles: Annotated[
        int, typer.Option("--titles", "-n", help="Number of title options to generate")
    ] = 3,
) -> None:
    """Install git hook for AI commit messages."""
    try:
        run_ai_commit("install", titles=titles)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@ai_commit_app.command()
def uninstall() -> None:
    """Uninstall git hook."""
    try:
        run_ai_commit("uninstall")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@ai_commit_app.command()
def hook(
    file: Annotated[str, typer.Argument(help="Commit message file")],
    source: Annotated[
        str | None, typer.Option("--source", help="Commit source")
    ] = None,
    titles: Annotated[int, typer.Option("--titles", help="Number of titles")] = 3,
    non_interactive: Annotated[
        bool, typer.Option("--non-interactive", help="Non-interactive mode")
    ] = False,
) -> None:
    """Hook handler (internal use by git)."""
    try:
        run_ai_commit(
            "hook",
            file=file,
            source=source,
            titles=titles,
            non_interactive=non_interactive,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@ai_commit_app.command()
def generate(
    titles: Annotated[
        int, typer.Option("--titles", "-n", help="Number of title options")
    ] = 3,
    apply: Annotated[
        bool, typer.Option("--apply", help="Write to COMMIT_EDITMSG")
    ] = False,
    json: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Generate commit message manually."""
    try:
        run_ai_commit("generate", titles=titles, apply=apply, json=json)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command()
def set(name: str, value: str | None = None) -> None:
    """Set a key."""
    try:
        set_key(name, value)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command()
def get(name: str) -> None:
    """Get a key."""
    try:
        value = get_key(name)
        if value:
            typer.echo(value)
        else:
            typer.echo(f"Key '{name}' not found", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("list")
def list_keys_cmd() -> None:
    """List all keys."""
    try:
        list_keys()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command()
def remove(name: str) -> None:
    """Remove a key."""
    try:
        remove_key(name)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("unlock")
def unlock_cmd(ttl: float = 8.0) -> None:
    """Unlock keystore."""
    try:
        unlock(ttl)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("lock")
def lock_cmd() -> None:
    """Lock keystore."""
    try:
        lock()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("migrate")
def migrate_cmd() -> None:
    """Migrate legacy key names to new standard format."""
    try:
        migrate_legacy_keys()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("providers")
def providers_cmd() -> None:
    """List all providers and their key status."""
    try:
        from rich.console import Console

        console = Console()

        providers = list_providers()
        default = get_default_provider()
        console.print("\n[bold]Provider Status:[/bold]")
        for provider, has_key in providers.items():
            status = "[green]✓[/green]" if has_key else "[dim]✗[/dim]"
            default_marker = " [cyan](default)[/cyan]" if provider == default else ""
            console.print(f"  {status} {provider.value}{default_marker}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@keys_app.command("set-default")
def set_default_cmd(provider: str) -> None:
    """Set the default LLM provider (anthropic or openai)."""
    try:
        # Normalize input
        provider_lower = provider.lower()
        provider_map = {p.value.lower(): p for p in Provider}

        if provider_lower not in provider_map:
            valid = ", ".join(p.value.lower() for p in Provider)
            typer.echo(
                f"Error: Unknown provider '{provider}'. Valid options: {valid}",
                err=True,
            )
            raise typer.Exit(1)

        set_default_provider(provider_map[provider_lower])
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
