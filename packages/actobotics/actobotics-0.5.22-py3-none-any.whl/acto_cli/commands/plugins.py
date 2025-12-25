from __future__ import annotations

import typer
from rich import print

from acto.plugins import PluginLoader

plugins_app = typer.Typer(help="List installed ACTO plugins.")


@plugins_app.command("list")
def list_plugins() -> None:
    """List installed ACTO plugins."""
    loader = PluginLoader()
    items = loader.list_plugins()
    if not items:
        print("[yellow]No plugins installed.[/yellow]")
        return
    print(f"[green]✓ Found {len(items)} plugin(s):[/green]")
    for p in items:
        print(f"  [cyan]{p.name}[/cyan] ({p.version}) -> {p.entrypoint}")
