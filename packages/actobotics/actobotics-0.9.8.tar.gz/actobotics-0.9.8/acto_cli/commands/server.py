from __future__ import annotations

import typer
from rich import print

server_app = typer.Typer(help="Run the ACTO verification API server.")


@server_app.command("run")
def run() -> None:
    """
    Run the API server.
    
    Note: This command requires the full installation with server dependencies.
    Install with: pip install actobotics[server] or clone the repo and run pip install -e ".[dev]"
    """
    try:
        from acto_server.run import main as run_server
    except ImportError:
        print("[red]Error:[/red] Server module not available.")
        print("")
        print("The server command is only available when running from the full repository.")
        print("For self-hosted deployments, clone the repo and install with:")
        print("")
        print("  [cyan]git clone https://github.com/actobotics/ACTO.git[/cyan]")
        print("  [cyan]pip install -e \".[dev]\"[/cyan]")
        print("")
        print("For SDK users: Use the hosted API at [cyan]https://api.actobotics.net[/cyan]")
        raise typer.Exit(1)
    
    print("[cyan]Starting ACTO server...[/cyan]")
    run_server()
