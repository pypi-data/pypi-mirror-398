from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from acto.pipeline import (
    ProofCreateStep,
    ProofPipeline,
    ProofVerifyStep,
    RegistryUpsertStep,
    TelemetryLoadStep,
    TelemetryNormalizeStep,
)
from acto.proof.models import ProofEnvelope

pipeline_app = typer.Typer(help="Pipeline-based workflows.")


@pipeline_app.command("run")
def run(
    task_id: str = typer.Option(..., help="Task ID"),
    source: str = typer.Option(..., help="Telemetry source (.jsonl/.csv)"),
    keypair: str = typer.Option("data/keys/acto_keypair.json", help="Keypair path"),
    robot_id: str | None = typer.Option(None, help="Robot ID"),
    run_id: str | None = typer.Option(None, help="Run ID"),
    out: str = typer.Option("data/proofs/proof.json", help="Write proof here"),
    store: bool = typer.Option(True, help="Store in registry"),
) -> None:
    steps = [TelemetryLoadStep(), TelemetryNormalizeStep(), ProofCreateStep(), ProofVerifyStep()]
    if store:
        steps.append(RegistryUpsertStep())

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Running pipeline...", total=None)
        pipe = ProofPipeline(steps)
        result = pipe.run(
            {"task_id": task_id, "source": source, "keypair": keypair, "robot_id": robot_id, "run_id": run_id}
        )
        progress.update(task, description="[green]Pipeline completed[/green]")

    env: ProofEnvelope = result.ctx["envelope"]

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(env.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]✓ Pipeline OK[/green] steps={result.steps}")
    if "proof_id" in result.ctx:
        print(f"[cyan]proof_id[/cyan]={result.ctx['proof_id']}")
