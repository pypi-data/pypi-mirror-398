from __future__ import annotations

import typer
from rich import print

from acto.access import SolanaTokenGate
from acto.config import Settings
from acto.errors import AccessError

access_app = typer.Typer(help="Token gating utilities.")


@access_app.command("check")
def check(
    owner: str = typer.Option(..., "--owner", "-o", help="Owner wallet address"),
    mint: str | None = typer.Option(
        None, "--mint", "-m", 
        help="Token mint address (default: configured ACTO token)"
    ),
    minimum: float | None = typer.Option(
        None, "--minimum", "-min",
        help="Minimum required token amount (default: 50000)"
    ),
    rpc: str | None = typer.Option(
        None, "--rpc", "-r",
        help="Solana RPC URL (default: configured RPC or Helius)"
    ),
) -> None:
    """Check whether a wallet meets the minimum token threshold.
    
    If --mint, --minimum, or --rpc are not provided, uses defaults from
    ACTO configuration (environment variables or config.toml).
    """
    settings = Settings()
    
    # Use configured defaults if not provided
    actual_mint = mint or settings.token_gating_mint
    actual_minimum = minimum if minimum is not None else settings.token_gating_minimum
    actual_rpc = rpc or settings.get_solana_rpc_url()
    
    try:
        gate = SolanaTokenGate(rpc_url=actual_rpc)
        decision = gate.decide(owner=owner, mint=actual_mint, minimum=actual_minimum)
        if decision.allowed:
            print(f"[green]✅ Access Allowed[/green]")
            print(f"   Wallet: {owner[:8]}...{owner[-4:]}")
            print(f"   Balance: {decision.balance:,.0f} tokens")
            print(f"   Required: {actual_minimum:,.0f} tokens")
        else:
            print(f"[red]❌ Access Denied[/red]")
            print(f"   Wallet: {owner[:8]}...{owner[-4:]}")
            print(f"   Balance: {decision.balance:,.0f} tokens")
            print(f"   Required: {actual_minimum:,.0f} tokens")
            print(f"   Reason: {decision.reason}")
    except AccessError as e:
        print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e

