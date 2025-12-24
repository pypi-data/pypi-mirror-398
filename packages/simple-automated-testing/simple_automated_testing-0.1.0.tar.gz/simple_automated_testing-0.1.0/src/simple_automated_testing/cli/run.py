from __future__ import annotations

import sys

import typer

from simple_automated_testing.core.executor import ExecutionError, run


def run_cmd(
    config: str = typer.Option(..., "--config", help="設定檔路徑"),
    pipeline: str | None = typer.Option(None, "--pipeline", help="指定 pipeline ID"),
) -> None:
    try:
        result = run(config_path=config, pipeline_id=pipeline)
    except ExecutionError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=2)

    summary = result.artifacts.get("humanSummary")
    if summary:
        typer.echo(summary)
    openapi_summary = result.artifacts.get("openApiSummary")
    if openapi_summary:
        typer.echo(openapi_summary)
    report_path = result.artifacts.get("humanReportPath")
    if report_path:
        typer.echo(f"Human report saved to: {report_path}")
    if result.status != "passed":
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)
