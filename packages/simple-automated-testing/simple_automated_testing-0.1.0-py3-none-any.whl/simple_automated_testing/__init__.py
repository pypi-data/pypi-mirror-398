"""Simple automated testing SDK/CLI package."""

from .sdk.builders import api_test, bq_data_test, bq_schema_test, pipeline
from .core.executor import run, run_with_config
from .reporting.human import render_human_summary
from .reporting.junit import render_junit

__all__ = [
    "api_test",
    "bq_data_test",
    "bq_schema_test",
    "pipeline",
    "run",
    "run_with_config",
    "render_human_summary",
    "render_junit",
]
