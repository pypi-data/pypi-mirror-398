from __future__ import annotations

from html import escape
from typing import List

from simple_automated_testing.contracts.models import RunResult, StepResult


def _format_step(step: StepResult) -> str:
    base = f"- {step.name} ({step.status}, {step.duration_ms}ms)"
    lines = []
    if step.status == "failed" and step.error:
        lines.append(f"{base} 失敗原因: {step.error}")
    else:
        lines.append(base)
    if step.details:
        for detail in step.details:
            lines.append(f"  - {detail}")
    return "\n".join(lines)


def render_human_summary(result: RunResult) -> str:
    result = result.with_counts()
    counts = result.counts
    header = (
        f"Run {result.run_id}: {result.status}\n"
        f"Passed: {counts.passed} Failed: {counts.failed} Skipped: {counts.skipped}\n"
        f"Started: {result.started_at}\n"
        f"Finished: {result.finished_at}"
    )

    lines: List[str] = [header, "", "Steps:"]
    for step in result.steps:
        lines.append(_format_step(step))
    return "\n".join(lines)


def render_human_html(result: RunResult) -> str:
    result = result.with_counts()
    counts = result.counts
    status_class = _status_class(result.status)
    step_rows = "\n".join(_format_step_html(step) for step in result.steps)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Human Report</title>
  <style>
    :root {{
      color-scheme: light;
      --text: #1f2937;
      --muted: #6b7280;
      --border: #e5e7eb;
      --bg: #ffffff;
      --success: #16a34a;
      --failed: #dc2626;
      --skipped: #6b7280;
    }}
    body {{
      font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
      color: var(--text);
      background: #f9fafb;
      margin: 0;
      padding: 24px;
    }}
    .container {{
      max-width: 860px;
      margin: 0 auto;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px 24px;
    }}
    header {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 16px;
    }}
    header h1 {{
      margin: 0 0 6px 0;
      font-size: 24px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 14px;
      display: grid;
      gap: 4px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
      background: #ffffff;
    }}
    .label {{
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }}
    .value {{
      font-size: 20px;
      font-weight: 600;
    }}
    .steps {{
      border-top: 1px solid var(--border);
      padding-top: 12px;
    }}
    .steps ul {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
    }}
    .step {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px 12px;
      background: #ffffff;
    }}
    .step header {{
      border: none;
      padding: 0;
      margin: 0;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }}
    .status {{
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
    }}
    .status.success {{
      color: var(--success);
    }}
    .status.failed {{
      color: var(--failed);
    }}
    .status.skipped {{
      color: var(--skipped);
    }}
    details {{
      margin-top: 8px;
      color: var(--failed);
      font-size: 13px;
    }}
    footer {{
      border-top: 1px solid var(--border);
      margin-top: 16px;
      padding-top: 12px;
      color: var(--muted);
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Human Report</h1>
      <div class="meta">
        <div>Run ID: {escape(result.run_id)}</div>
        <div class="status {status_class}">Status: {escape(result.status)}</div>
        <div>Started: {escape(result.started_at)}</div>
        <div>Finished: {escape(result.finished_at)}</div>
      </div>
    </header>

    <section class="summary">
      <div class="card">
        <div class="label">Passed</div>
        <div class="value">{counts.passed}</div>
      </div>
      <div class="card">
        <div class="label">Failed</div>
        <div class="value">{counts.failed}</div>
      </div>
      <div class="card">
        <div class="label">Skipped</div>
        <div class="value">{counts.skipped}</div>
      </div>
    </section>

    <section class="steps">
      <h2>Steps</h2>
      <ul>
        {step_rows}
      </ul>
    </section>

    <footer>Generated by simple-automated-testing</footer>
  </div>
</body>
</html>
"""


def _status_class(status: str) -> str:
    if status == "passed":
        return "success"
    if status == "failed":
        return "failed"
    return "skipped"


def _format_step_html(step: StepResult) -> str:
    status_class = _status_class(step.status)
    name = escape(step.name)
    duration = step.duration_ms
    status = escape(step.status)
    details_html = ""
    if step.details:
        detail_items = "".join(f"<li>{escape(item)}</li>" for item in step.details)
        details_html = f"<details><summary>詳細資訊</summary><ul>{detail_items}</ul></details>"
    if step.status == "failed" and step.error:
        error = escape(step.error)
        return (
            "<li class=\"step\">"
            f"<header><span>{name}</span><span class=\"status {status_class}\">{status}</span></header>"
            f"<div>{duration}ms</div>"
            f"<details><summary>失敗原因</summary><div>{error}</div></details>"
            f"{details_html}"
            "</li>"
        )
    return (
        "<li class=\"step\">"
        f"<header><span>{name}</span><span class=\"status {status_class}\">{status}</span></header>"
        f"<div>{duration}ms</div>"
        f"{details_html}"
        "</li>"
    )
