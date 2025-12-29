from __future__ import annotations

import typer
from rich import print

from acto.crypto import KeyPair, save_keypair

keys_app = typer.Typer(help="Key management.")


@keys_app.command("generate")
def generate(out: str = typer.Option("data/keys/acto_keypair.json", help="Output keypair path")) -> None:
    """Generate a new Ed25519 keypair."""
    kp = KeyPair.generate()
    save_keypair(out, kp)
    print(f"[green]✓ Saved keypair:[/green] {out}")
    print(f"[cyan]Public key (b64):[/cyan] {kp.public_key_b64}")
