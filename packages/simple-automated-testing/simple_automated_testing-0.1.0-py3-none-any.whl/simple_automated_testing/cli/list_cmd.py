from __future__ import annotations

import typer

from simple_automated_testing.cli.errors import CliError
from simple_automated_testing.config.discovery import discover_pipelines, discover_tests
from simple_automated_testing.config.loader import load_config
from simple_automated_testing.config.validation import validate_config


def list_cmd(config: str = typer.Option(..., "--config", help="設定檔路徑")) -> None:
    try:
        config_data = validate_config(load_config(config))
        tests = discover_tests(config_data)
        pipelines = discover_pipelines(config_data)

        if not tests and not pipelines:
            raise CliError("沒有可列出的測試或 pipeline", exit_code=2)

        if tests:
            typer.echo("Tests:")
            for test in tests:
                typer.echo(f"- {test.get('name', test.get('type'))}")
        if pipelines:
            typer.echo("Pipelines:")
            for pipe in pipelines:
                typer.echo(f"- {pipe.get('id', pipe.get('name'))}")
    except CliError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=exc.exit_code)
