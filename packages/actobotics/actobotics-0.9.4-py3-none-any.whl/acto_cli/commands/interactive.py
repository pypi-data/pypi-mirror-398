from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from acto.access import SolanaTokenGate
from acto.config import Settings
from acto.crypto import KeyPair, load_keypair, save_keypair
from acto.errors import AccessError, ProofError, TelemetryError
from acto.proof import ProofEnvelope, create_proof
from acto.registry import ProofRegistry
from acto.telemetry import CsvTelemetryParser, JsonlTelemetryParser

console = Console()
interactive_app = typer.Typer(help="Interactive mode for ACTO CLI.")


def _print_menu() -> None:
    """Print the interactive menu."""
    table = Table(title="ACTO Interactive Mode", show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    table.add_row("1", "Generate keypair")
    table.add_row("2", "Create proof")
    table.add_row("3", "Verify proof")
    table.add_row("4", "List proofs in registry")
    table.add_row("5", "Get proof from registry")
    table.add_row("6", "Check token access")
    table.add_row("q", "Quit")

    console.print(table)


def _handle_generate_keypair() -> None:
    """Handle keypair generation."""
    console.print("\n[bold cyan]Generate Keypair[/bold cyan]")
    out = Prompt.ask("Output path", default="data/keys/acto_keypair.json")
    try:
        kp = KeyPair.generate()
        save_keypair(out, kp)
        console.print(f"[green]✓ Keypair generated: {out}[/green]")
        console.print(f"[cyan]Public key (b64):[/cyan] {kp.public_key_b64}")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _handle_create_proof() -> None:
    """Handle proof creation."""
    console.print("\n[bold cyan]Create Proof[/bold cyan]")
    task_id = Prompt.ask("Task ID")
    source = Prompt.ask("Telemetry source file")
    keypair = Prompt.ask("Keypair path", default="data/keys/acto_keypair.json")
    robot_id = Prompt.ask("Robot ID (optional)", default="")
    run_id = Prompt.ask("Run ID (optional)", default="")
    out = Prompt.ask("Output path", default="data/proofs/proof.json")
    registry = Confirm.ask("Store in registry?", default=True)

    try:
        kp = load_keypair(keypair)
        p = Path(source)
        if p.suffix.lower() == ".jsonl":
            parser = JsonlTelemetryParser()
        elif p.suffix.lower() == ".csv":
            parser = CsvTelemetryParser()
        else:
            console.print("[red]Unsupported telemetry file type. Use .jsonl or .csv[/red]")
            return

        bundle = parser.parse(
            source,
            task_id=task_id,
            robot_id=robot_id if robot_id else None,
            run_id=run_id if run_id else None,
        )

        env = create_proof(bundle, kp.private_key_b64, kp.public_key_b64)

        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(env.model_dump_json(indent=2), encoding="utf-8")

        console.print(f"[green]✓ Proof written:[/green] {out}")
        console.print(f"[cyan]Payload hash:[/cyan] {env.payload.payload_hash}")

        if registry:
            reg = ProofRegistry()
            proof_id = reg.upsert(env)
            console.print(f"[green]Stored in registry:[/green] {proof_id}")
    except (TelemetryError, ProofError) as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _handle_verify_proof() -> None:
    """Handle proof verification - now requires API."""
    console.print("\n[bold yellow]⚠ Local Verification Removed[/bold yellow]")
    console.print()
    console.print("All proof verification must now be done through the ACTO API.")
    console.print()
    console.print("[cyan]Option 1: Use the Python SDK[/cyan]")
    console.print("  from acto.client import ACTOClient")
    console.print("  client = ACTOClient(api_key='...', wallet_address='...')")
    console.print("  result = client.verify(envelope)")
    console.print()
    console.print("[cyan]Option 2: Use the Dashboard[/cyan]")
    console.print("  Visit: https://api.actobotics.net/dashboard")
    console.print("  Use the API Playground to verify proofs")
    console.print()
    console.print("[cyan]Get your API key at:[/cyan] https://api.actobotics.net/dashboard")


def _handle_list_proofs() -> None:
    """Handle listing proofs."""
    console.print("\n[bold cyan]List Proofs[/bold cyan]")
    limit = Prompt.ask("Limit", default="50")
    try:
        reg = ProofRegistry()
        items = reg.list(limit=int(limit))
        console.print(json.dumps(items, indent=2))
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _handle_get_proof() -> None:
    """Handle getting a proof."""
    console.print("\n[bold cyan]Get Proof[/bold cyan]")
    proof_id = Prompt.ask("Proof ID")
    try:
        reg = ProofRegistry()
        env = reg.get(proof_id)
        console.print(env.model_dump_json(indent=2))
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _handle_check_access() -> None:
    """Handle access check."""
    console.print("\n[bold cyan]Check Token Access[/bold cyan]")
    rpc = Prompt.ask("Solana RPC URL")
    owner = Prompt.ask("Owner wallet address")
    mint = Prompt.ask("Token mint address")
    minimum = Prompt.ask("Minimum required token amount")
    try:
        gate = SolanaTokenGate(rpc_url=rpc)
        decision = gate.decide(owner=owner, mint=mint, minimum=float(minimum))
        if decision.allowed:
            console.print(f"[green]Allowed[/green] balance={decision.balance}")
        else:
            console.print(f"[red]Denied[/red] reason={decision.reason} balance={decision.balance}")
    except AccessError as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@interactive_app.command("start")
def start() -> None:
    """Start interactive mode."""
    settings = Settings()
    console.print(
        Panel(
            f"[bold green]ACTO Interactive Mode[/bold green]\n"
            f"Version: {settings.proof_version}\n"
            f"Database: {settings.db_url}",
            title="Welcome",
            border_style="cyan",
        )
    )

    while True:
        _print_menu()
        choice = Prompt.ask("\n[bold]Select an option[/bold]", default="q").lower().strip()

        if choice == "q":
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)
        elif choice == "1":
            _handle_generate_keypair()
        elif choice == "2":
            _handle_create_proof()
        elif choice == "3":
            _handle_verify_proof()
        elif choice == "4":
            _handle_list_proofs()
        elif choice == "5":
            _handle_get_proof()
        elif choice == "6":
            _handle_check_access()
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

        if not Confirm.ask("\nContinue?", default=True):
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)

