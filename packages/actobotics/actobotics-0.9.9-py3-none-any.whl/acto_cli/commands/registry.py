from __future__ import annotations

import json

import typer
from rich import print

from acto.registry import ProofRegistry

registry_app = typer.Typer(help="Local proof registry utilities.")


@registry_app.command("list")
def list_cmd(limit: int = typer.Option(50, help="Max items")) -> None:
    """List proofs in the registry."""
    reg = ProofRegistry()
    items = reg.list(limit=limit)
    if items:
        print(f"[green]✓ Found {len(items)} proof(s)[/green]")
        print(json.dumps(items, indent=2))
    else:
        print("[yellow]No proofs found in registry.[/yellow]")


@registry_app.command("get")
def get_cmd(proof_id: str = typer.Option(..., help="Proof ID")) -> None:
    """Get a proof from the registry by ID."""
    reg = ProofRegistry()
    env = reg.get(proof_id)
    print(f"[green]✓ Proof found:[/green] {proof_id}")
    print(env.model_dump_json(indent=2))
