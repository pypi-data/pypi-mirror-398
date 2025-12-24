from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class Diff:
    rule: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    samples: List[Any] = field(default_factory=list)


@dataclass(slots=True)
class AssertionResult:
    name: str
    passed: bool
    diffs: List[Diff] = field(default_factory=list)


@dataclass(slots=True)
class StepResult:
    step_id: str
    name: str
    status: str
    duration_ms: int
    assertions: List[AssertionResult] = field(default_factory=list)
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RunCounts:
    passed: int
    failed: int
    skipped: int


@dataclass(slots=True)
class RunResult:
    run_id: str
    status: str
    started_at: str
    finished_at: str
    steps: List[StepResult] = field(default_factory=list)
    counts: Optional[RunCounts] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def with_counts(self) -> "RunResult":
        if self.counts is not None:
            return self
        passed = sum(1 for step in self.steps if step.status == "passed")
        failed = sum(1 for step in self.steps if step.status == "failed")
        skipped = sum(1 for step in self.steps if step.status == "skipped")
        self.counts = RunCounts(passed=passed, failed=failed, skipped=skipped)
        return self
