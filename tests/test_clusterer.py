import numpy as np
import pytest
from vlsi_report_cluster.clusterer import ClusterResult, cluster_embeddings


def _make_clustered_embeddings(
    centers: np.ndarray,
    counts: list[int],
    scale: float = 0.05,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    clusters = [
        rng.normal(loc=center, scale=scale, size=(count, centers.shape[1]))
        for center, count in zip(centers, counts)
    ]
    return np.vstack(clusters)


def test_cluster_distinct_groups():
    """Verify distinct violation types form multiple clusters."""
    centers = np.array(
        [
            [0.0, 0.0],
            [6.0, 6.0],
            [0.0, 6.0],
        ]
    )
    embeddings = _make_clustered_embeddings(centers, [15, 15, 15], scale=0.08, seed=1)

    result = cluster_embeddings(embeddings)

    assert result is not None
    assert result.n_clusters >= 2


def test_cluster_labels_shape():
    """Ensure labels length matches embeddings length."""
    centers = np.array([[0.0, 0.0], [5.0, 5.0]])
    embeddings = _make_clustered_embeddings(centers, [6, 6], scale=0.05, seed=2)

    result = cluster_embeddings(embeddings)

    assert result is not None
    assert len(result.labels) == embeddings.shape[0]


def test_cluster_noise_points():
    """Confirm some outliers are labeled as noise (-1)."""
    centers = np.array([[0.0, 0.0], [5.0, 5.0]])
    embeddings = _make_clustered_embeddings(centers, [10, 10], scale=0.05, seed=3)
    outliers = np.array(
        [
            [100.0, 100.0],
            [-120.0, 90.0],
            [80.0, -110.0],
        ]
    )
    embeddings = np.vstack([embeddings, outliers])

    result = cluster_embeddings(embeddings)

    assert result is not None
    assert -1 in result.labels


def test_cluster_small_report_fallback():
    """Return None for reports with fewer than 6 embeddings."""
    embeddings = np.random.default_rng(4).normal(size=(5, 2))

    result = cluster_embeddings(embeddings)

    assert result is None


def test_cluster_high_noise_fallback():
    """Return None when more than 80% of points are noise."""
    embeddings = np.array([[i * 12.0, i * -12.0] for i in range(20)], dtype=float)

    result = cluster_embeddings(embeddings, min_cluster_size=4, min_samples=2)

    assert result is None


def test_cluster_min_cluster_size_parameter():
    """Validate min_cluster_size changes clustering outcome."""
    centers = np.array([[0.0, 0.0], [7.0, 7.0]])
    embeddings = _make_clustered_embeddings(centers, [5, 5], scale=0.05, seed=5)

    result_small = cluster_embeddings(embeddings, min_cluster_size=3, min_samples=2)
    result_large = cluster_embeddings(embeddings, min_cluster_size=6, min_samples=2)

    assert result_small is not None
    assert result_large is None


def test_cluster_returns_metadata():
    """Ensure clustering result exposes metadata fields."""
    centers = np.array([[0.0, 0.0], [5.5, 5.5]])
    embeddings = _make_clustered_embeddings(centers, [6, 6], scale=0.05, seed=6)

    result = cluster_embeddings(embeddings)

    if result is None:
        pytest.fail("Expected ClusterResult for metadata checks.")

    assert isinstance(result, ClusterResult)
    assert hasattr(result, "n_clusters")
    assert hasattr(result, "n_noise")
