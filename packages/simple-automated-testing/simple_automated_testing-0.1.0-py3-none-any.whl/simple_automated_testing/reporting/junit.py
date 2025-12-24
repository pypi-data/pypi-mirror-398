from __future__ import annotations

import xml.etree.ElementTree as ET

from simple_automated_testing.contracts.models import RunResult


def render_junit(result: RunResult) -> str:
    result = result.with_counts()
    counts = result.counts

    testsuite = ET.Element(
        "testsuite",
        {
            "name": "simple-automated-testing",
            "tests": str(len(result.steps)),
            "failures": str(counts.failed),
            "skipped": str(counts.skipped),
        },
    )

    for step in result.steps:
        case = ET.SubElement(
            testsuite,
            "testcase",
            {
                "name": step.name,
                "time": f"{step.duration_ms / 1000:.3f}",
            },
        )
        if step.status == "skipped":
            ET.SubElement(case, "skipped")
        elif step.status == "failed":
            failure = ET.SubElement(case, "failure", {"message": step.error or "failed"})
            if step.assertions:
                details = []
                for assertion in step.assertions:
                    for diff in assertion.diffs:
                        details.append(f"{diff.rule}: {diff.message}")
                failure.text = "\n".join(details)

    tree = ET.ElementTree(testsuite)
    return ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True).decode("utf-8")
