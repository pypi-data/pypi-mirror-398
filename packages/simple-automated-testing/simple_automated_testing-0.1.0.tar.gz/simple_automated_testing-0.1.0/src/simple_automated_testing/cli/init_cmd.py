from __future__ import annotations

from pathlib import Path

import typer
import yaml

from simple_automated_testing.cli.errors import CliError


def init_cmd(
    output: str = typer.Option("simple-test.yaml", "--output", help="輸出設定檔路徑"),
) -> None:
    try:
        output_path = Path(output)
        if output_path.exists():
            raise CliError(f"檔案已存在：{output}", exit_code=2)

        sample = {
            "projectName": "sample",
            "apiTargets": [{"id": "main", "baseUrl": "https://example.com"}],
            "bigQuery": {"projectId": "your-project", "dataset": "your_dataset"},
            "identities": [
                {
                    "name": "default",
                    "isDefault": True,
                    "serviceAccountKeyPath": "path/to/service-account.json",
                }
            ],
            "reporting": {
                "junitEnabled": True,
                "junitOutputPath": "./test-results/junit.xml",
                "humanSummary": True,
                "humanReportEnabled": True,
                "humanReportOutputDir": "./custom-reports",
                "humanReportFileName": "human-report.html",
            },
            "tests": [
                {
                    "type": "api",
                    "name": "health",
                    "target": "main",
                    "path": "/health",
                    "assertions": [{"type": "status_code", "expected": 200}],
                },
                {
                    "type": "bigquery.schema",
                    "name": "schema",
                    "table": "project.dataset.table",
                    "identity": "default",
                    "expectedSchema": [{"name": "id", "type": "STRING", "mode": "REQUIRED"}],
                },
            ],
        }

        output_path.write_text(yaml.safe_dump(sample, allow_unicode=True), encoding="utf-8")
        typer.echo(f"已建立範例設定檔：{output}")
    except CliError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=exc.exit_code)
