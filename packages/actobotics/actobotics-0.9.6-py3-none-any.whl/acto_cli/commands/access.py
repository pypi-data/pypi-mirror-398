from __future__ import annotations

import typer
from rich import print

from acto.access import SolanaTokenGate
from acto.errors import AccessError

access_app = typer.Typer(help="Token gating utilities.")


@access_app.command("check")
def check(
    rpc: str = typer.Option(..., help="Solana RPC URL"),
    owner: str = typer.Option(..., help="Owner wallet address"),
    mint: str = typer.Option(..., help="Token mint address"),
    minimum: float = typer.Option(..., help="Minimum required token amount"),
) -> None:
    """Check whether a wallet meets the minimum token threshold."""
    try:
        gate = SolanaTokenGate(rpc_url=rpc)
        decision = gate.decide(owner=owner, mint=mint, minimum=minimum)
        if decision.allowed:
            print(f"[green]Allowed[/green] balance={decision.balance}")
        else:
            print(f"[red]Denied[/red] reason={decision.reason} balance={decision.balance}")
    except AccessError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(code=1) from e

