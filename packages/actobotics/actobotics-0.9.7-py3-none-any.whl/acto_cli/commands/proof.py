from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from acto.crypto import load_keypair
from acto.errors import ProofError, TelemetryError
from acto.proof import ProofEnvelope, create_proof
from acto.registry import ProofRegistry
from acto.telemetry import CsvTelemetryParser, JsonlTelemetryParser

proof_app = typer.Typer(help="Create ACTO proofs. Verification is only available via the API.")


def _select_parser(source: str):
    p = Path(source)
    if p.suffix.lower() == ".jsonl":
        return JsonlTelemetryParser()
    if p.suffix.lower() == ".csv":
        return CsvTelemetryParser()
    raise typer.BadParameter("Unsupported telemetry file type. Use .jsonl or .csv")


@proof_app.command("create")
def create(
    task_id: str = typer.Option(..., help="Task ID"),
    source: str = typer.Option(..., help="Telemetry source file (.jsonl or .csv)"),
    keypair: str = typer.Option("data/keys/acto_keypair.json", help="Keypair path"),
    robot_id: str | None = typer.Option(None, help="Robot ID"),
    run_id: str | None = typer.Option(None, help="Run ID"),
    out: str = typer.Option("data/proofs/proof.json", help="Output proof path"),
    registry: bool = typer.Option(True, help="Store proof in local registry"),
) -> None:
    """Create a signed proof envelope."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task1 = progress.add_task("Loading keypair...", total=None)
            kp = load_keypair(keypair)
            progress.update(task1, description="[green]Keypair loaded[/green]")

            task2 = progress.add_task("Parsing telemetry...", total=None)
            parser = _select_parser(source)
            bundle = parser.parse(
                source,
                task_id=task_id,
                robot_id=robot_id,
                run_id=run_id,
            )
            progress.update(task2, description="[green]Telemetry parsed[/green]")

            task3 = progress.add_task("Creating proof...", total=None)
            env = create_proof(bundle, kp.private_key_b64, kp.public_key_b64)
            progress.update(task3, description="[green]Proof created[/green]")

            task4 = progress.add_task("Writing proof to file...", total=None)
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(env.model_dump_json(indent=2), encoding="utf-8")
            progress.update(task4, description="[green]Proof written[/green]")

            if registry:
                task5 = progress.add_task("Storing in registry...", total=None)
                reg = ProofRegistry()
                proof_id = reg.upsert(env)
                progress.update(task5, description="[green]Stored in registry[/green]")

        print(f"[green]✓ Proof written:[/green] {out}")
        print(f"[cyan]Payload hash:[/cyan] {env.payload.payload_hash}")

        if registry:
            print(f"[green]✓ Stored in registry:[/green] {proof_id}")

    except (TelemetryError, ProofError) as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(code=1) from e


@proof_app.command("verify")
def verify(
    proof: str = typer.Option(..., help="Proof JSON file"),
) -> None:
    """
    Verify a proof envelope.
    
    NOTE: Local verification has been removed. Use the ACTO API instead.
    """
    print("[yellow]⚠ Local verification has been removed.[/yellow]")
    print()
    print("All proof verification must now be done through the ACTO API.")
    print()
    print("[cyan]Option 1: Use the Python SDK[/cyan]")
    print("  from acto.client import ACTOClient")
    print("  client = ACTOClient(api_key='...', wallet_address='...')")
    print("  result = client.verify(envelope)")
    print()
    print("[cyan]Option 2: Use the Dashboard[/cyan]")
    print("  Visit: https://api.actobotics.net/dashboard")
    print("  Use the API Playground to verify proofs")
    print()
    print("[cyan]Get your API key at:[/cyan] https://api.actobotics.net/dashboard")
    raise typer.Exit(code=1)
