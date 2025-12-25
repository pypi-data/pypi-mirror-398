from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from acto.proof import ProofEnvelope, verify_proof
from acto.reputation import ReputationScorer

score_app = typer.Typer(help="Reputation scoring.")


@score_app.command("compute")
def compute(proof: str = typer.Option(..., help="Proof JSON file")) -> None:
    """Compute reputation score for a proof."""
    env = ProofEnvelope.model_validate_json(Path(proof).read_text(encoding="utf-8"))
    verify_proof(env)
    scorer = ReputationScorer()
    result = scorer.score(env)
    print(f"[green]✓ Reputation score:[/green] [cyan]{result.score}[/cyan]")
    if result.reasons:
        print(f"[yellow]Reasons:[/yellow] {result.reasons}")
