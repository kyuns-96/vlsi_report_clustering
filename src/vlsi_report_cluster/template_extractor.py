"""Template extractor module using Drain3."""

# pyright: reportMissingImports=false

from dataclasses import dataclass

import numpy as np
from drain3 import TemplateMiner


@dataclass
class ClusterTemplate:
    cluster_id: int
    template: str
    count: int
    values: list[list[str]]


@dataclass
class ExtractionResult:
    clusters: list[ClusterTemplate]
    noise_lines: list[str]
    is_fallback: bool


def _extract_values(
    miner: TemplateMiner,
    template: str,
    cluster_lines: list[str],
) -> list[list[str]]:
    values: list[list[str]] = []
    for line in cluster_lines:
        extracted = miner.drain.extract_parameters(template, line)
        values.append(list(extracted))
    return values


def extract_templates(
    lines: list[str],
    labels: np.ndarray | None = None,
) -> ExtractionResult:
    if labels is None:
        miner = TemplateMiner()
        templates: dict[int, list[str]] = {}
        for line in lines:
            result = miner.add_log_message(line)
            cluster_id = int(result["cluster_id"])
            templates.setdefault(cluster_id, []).append(line)

        clusters = []
        for cluster_id, cluster_lines in templates.items():
            template = miner.drain.clusters[cluster_id].get_template()
            values = _extract_values(miner, template, cluster_lines)
            clusters.append(
                ClusterTemplate(
                    cluster_id=cluster_id,
                    template=template,
                    count=len(cluster_lines),
                    values=values,
                )
            )

        return ExtractionResult(
            clusters=clusters,
            noise_lines=[],
            is_fallback=True,
        )

    noise_lines = [
        lines[index]
        for index, label in enumerate(labels)
        if int(label) == -1
    ]

    cluster_map: dict[int, list[str]] = {}
    for index, label in enumerate(labels):
        label_id = int(label)
        if label_id == -1:
            continue
        cluster_map.setdefault(label_id, []).append(lines[index])

    clusters: list[ClusterTemplate] = []
    for cluster_id, cluster_lines in cluster_map.items():
        miner = TemplateMiner()
        for line in cluster_lines:
            miner.add_log_message(line)

        if not miner.drain.clusters:
            continue

        drain_cluster = next(iter(miner.drain.clusters.values()))
        template = drain_cluster.get_template()
        values = _extract_values(miner, template, cluster_lines)
        clusters.append(
            ClusterTemplate(
                cluster_id=cluster_id,
                template=template,
                count=len(cluster_lines),
                values=values,
            )
        )

    return ExtractionResult(
        clusters=clusters,
        noise_lines=noise_lines,
        is_fallback=False,
    )
