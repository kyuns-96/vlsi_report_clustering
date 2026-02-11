import numpy as np
import pytest  # type: ignore
from vlsi_report_cluster.template_extractor import (  # type: ignore
    ClusterTemplate,
    ExtractionResult,
    extract_templates,
)


def _get_cluster(
    clusters: list[ClusterTemplate],
    cluster_id: int,
) -> ClusterTemplate:
    for cluster in clusters:
        if cluster.cluster_id == cluster_id:
            return cluster
    pytest.fail(f"Expected cluster_id {cluster_id} in extraction results.")
    raise AssertionError("Unreachable")


def test_extract_template_from_similar_lines():
    lines = [
        "Warning: signal CLK unconnected at module CPU_0",
        "Warning: signal RST unconnected at module CPU_0",
        "Warning: signal EN unconnected at module CPU_0",
        "Warning: signal DATA unconnected at module CPU_0",
        "Warning: signal ADDR unconnected at module CPU_0",
    ]
    labels = np.zeros(len(lines), dtype=np.int32)

    result = extract_templates(lines, labels)

    assert isinstance(result, ExtractionResult)
    assert result.is_fallback is False
    assert result.noise_lines == []
    assert len(result.clusters) == 1

    cluster = result.clusters[0]
    assert isinstance(cluster, ClusterTemplate)
    assert cluster.cluster_id == 0
    assert cluster.count == len(lines)
    assert "Warning: signal" in cluster.template
    assert "<*>" in cluster.template


def test_extract_values_from_template():
    lines = [
        "Error: latch inferred for signal DATA in module MEM_1",
        "Error: latch inferred for signal CTRL in module MEM_2",
        "Error: latch inferred for signal ADDR in module MEM_3",
    ]
    labels = np.zeros(len(lines), dtype=np.int32)

    result = extract_templates(lines, labels)
    cluster = result.clusters[0]
    wildcard_count = cluster.template.count("<*>")

    assert wildcard_count >= 2
    assert len(cluster.values) == len(lines)
    assert all(isinstance(values, (list, tuple)) for values in cluster.values)
    assert all(len(values) == wildcard_count for values in cluster.values)
    assert all(
        all(isinstance(value, str) for value in values) for values in cluster.values
    )

    expected_values = [
        ("DATA", "MEM_1"),
        ("CTRL", "MEM_2"),
        ("ADDR", "MEM_3"),
    ]
    for actual_values, expected_pair in zip(cluster.values, expected_values):
        for token in expected_pair:
            assert token in actual_values


def test_fresh_drain_per_cluster():
    lines = [
        "Warning: signal CLK unconnected at module CPU_0",
        "Warning: signal RST unconnected at module CPU_0",
        "Warning: signal CLK unconnected at module GPU_0",
        "Warning: signal RST unconnected at module GPU_0",
    ]
    labels = np.array([0, 0, 1, 1], dtype=np.int32)

    result = extract_templates(lines, labels)

    cluster_cpu = _get_cluster(result.clusters, 0)
    cluster_gpu = _get_cluster(result.clusters, 1)

    assert "CPU_0" in cluster_cpu.template
    assert "GPU_0" not in cluster_cpu.template
    assert "GPU_0" in cluster_gpu.template
    assert "CPU_0" not in cluster_gpu.template


def test_extract_from_all_clusters():
    lines = [
        "Warning: signal CLK unconnected at module CPU_0",
        "Warning: signal RST unconnected at module CPU_0",
        "Error: latch inferred for signal DATA in module MEM_1",
        "Error: latch inferred for signal ADDR in module MEM_2",
    ]
    labels = np.array([0, 0, 1, 1], dtype=np.int32)

    result = extract_templates(lines, labels)

    assert len(result.clusters) == 2
    cluster_warning = _get_cluster(result.clusters, 0)
    cluster_error = _get_cluster(result.clusters, 1)

    assert cluster_warning.count == 2
    assert cluster_error.count == 2
    assert "Warning:" in cluster_warning.template
    assert "Error:" in cluster_error.template


def test_extract_single_line_cluster():
    single_line = "Warning: signal CLK unconnected at module CPU_0"
    lines = [
        single_line,
        "Error: latch inferred for signal DATA in module MEM_1",
        "Error: latch inferred for signal ADDR in module MEM_2",
    ]
    labels = np.array([0, 1, 1], dtype=np.int32)

    result = extract_templates(lines, labels)
    cluster_single = _get_cluster(result.clusters, 0)

    assert cluster_single.count == 1
    assert cluster_single.template == single_line


def test_extract_noise_lines():
    noise_line = "Info: waived violation for signal TEST in module IO_0"
    lines = [
        "Warning: signal CLK unconnected at module CPU_0",
        noise_line,
        "Warning: signal RST unconnected at module CPU_0",
    ]
    labels = np.array([0, -1, 0], dtype=np.int32)

    result = extract_templates(lines, labels)

    assert result.noise_lines == [noise_line]
    assert all(cluster.cluster_id != -1 for cluster in result.clusters)


def test_drain3_only_mode():
    lines = [
        "Warning: signal CLK unconnected at module CPU_0",
        "Warning: signal RST unconnected at module CPU_0",
        "Warning: signal EN unconnected at module CPU_0",
    ]

    result = extract_templates(lines)

    assert result.is_fallback is True
    assert result.noise_lines == []
    assert len(result.clusters) == 1

    cluster = result.clusters[0]
    assert cluster.count == len(lines)
    assert "<*>" in cluster.template
