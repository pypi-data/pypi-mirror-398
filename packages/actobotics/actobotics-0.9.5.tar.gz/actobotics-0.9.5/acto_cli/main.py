from __future__ import annotations

import typer

from acto.config import Settings
from acto.logging import configure_logging
from acto_cli.commands.access import access_app
from acto_cli.commands.completion import completion_app
from acto_cli.commands.interactive import interactive_app
from acto_cli.commands.keys import keys_app
from acto_cli.commands.pipeline import pipeline_app
from acto_cli.commands.plugins import plugins_app
from acto_cli.commands.proof import proof_app
from acto_cli.commands.registry import registry_app
from acto_cli.commands.score import score_app
from acto_cli.commands.server import server_app

app = typer.Typer(add_completion=True, help="ACTO CLI")

app.add_typer(keys_app, name="keys")
app.add_typer(proof_app, name="proof")
app.add_typer(server_app, name="server")
app.add_typer(access_app, name="access")
app.add_typer(registry_app, name="registry")
app.add_typer(score_app, name="score")
app.add_typer(plugins_app, name="plugins")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(interactive_app, name="interactive")
app.add_typer(completion_app, name="completion")


@app.callback()
def _init(
    log_level: str = typer.Option(None, help="Override log level"),
    json_logs: bool = typer.Option(False, help="Enable JSON logs"),
):
    settings = Settings()
    configure_logging(log_level or settings.log_level, json_logs or settings.json_logs)
