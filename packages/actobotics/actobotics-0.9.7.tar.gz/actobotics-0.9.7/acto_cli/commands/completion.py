from __future__ import annotations

import typer
from rich import print

completion_app = typer.Typer(help="Shell completion installation.")


@completion_app.command("install")
def install(
    shell: str = typer.Option(..., help="Shell type: bash, zsh, fish, or powershell"),
) -> None:
    """Install shell completion for ACTO CLI."""
    import subprocess
    import sys

    shell_map = {
        "bash": "bash",
        "zsh": "zsh",
        "fish": "fish",
        "powershell": "powershell",
    }

    if shell not in shell_map:
        print(f"[red]Unsupported shell: {shell}[/red]")
        print("[yellow]Supported shells: bash, zsh, fish, powershell[/yellow]")
        raise typer.Exit(code=1)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "typer_cli", "acto_cli.main:app", shell],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"[green]✓ Completion script for {shell}:[/green]")
        print()
        print(result.stdout)
        print()
        print(f"[yellow]To enable completion, add the above script to your {shell} configuration file.[/yellow]")
    except subprocess.CalledProcessError as e:
        print(f"[red]Error generating completion:[/red] {e.stderr}")
        raise typer.Exit(code=1) from e
    except FileNotFoundError:
        print("[red]typer-cli not found. Install it with: pip install typer-cli[/red]")
        raise typer.Exit(code=1) from None


@completion_app.command("show")
def show(
    shell: str = typer.Option(..., help="Shell type: bash, zsh, fish, or powershell"),
) -> None:
    """Show shell completion script without installing."""
    import subprocess
    import sys

    shell_map = {
        "bash": "bash",
        "zsh": "zsh",
        "fish": "fish",
        "powershell": "powershell",
    }

    if shell not in shell_map:
        print(f"[red]Unsupported shell: {shell}[/red]")
        print("[yellow]Supported shells: bash, zsh, fish, powershell[/yellow]")
        raise typer.Exit(code=1)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "typer_cli", "acto_cli.main:app", shell],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[red]Error generating completion:[/red] {e.stderr}")
        raise typer.Exit(code=1) from e
    except FileNotFoundError:
        print("[red]typer-cli not found. Install it with: pip install typer-cli[/red]")
        raise typer.Exit(code=1) from None

