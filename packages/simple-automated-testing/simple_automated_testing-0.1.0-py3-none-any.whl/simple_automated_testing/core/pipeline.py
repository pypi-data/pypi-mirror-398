from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class PipelineStep:
    type: str
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Pipeline:
    pipeline_id: str
    name: str
    steps: List[PipelineStep]
    mode: str = "failFast"


def from_dict(data: Dict[str, Any]) -> Pipeline:
    steps = [
        PipelineStep(type=step.get("type"), name=step.get("name", step.get("type", "step")), payload=step)
        for step in data.get("steps", [])
    ]
    return Pipeline(
        pipeline_id=data.get("id", "pipeline"),
        name=data.get("name", data.get("id", "pipeline")),
        steps=steps,
        mode=data.get("mode", "failFast"),
    )
