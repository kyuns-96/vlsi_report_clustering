"""Clusterer module for HDBSCAN clustering."""

# pyright: reportMissingImports=false

from dataclasses import dataclass

import numpy as np
from hdbscan import HDBSCAN
from numpy.typing import NDArray


@dataclass
class ClusterResult:
    """Clustering result metadata and labels."""

    labels: NDArray[np.int32]
    n_clusters: int
    n_noise: int
    is_fallback: bool


def cluster_embeddings(
    embeddings: np.ndarray,
    min_cluster_size: int = 3,
    min_samples: int = 2,
) -> ClusterResult | None:
    """Cluster embeddings with HDBSCAN and apply fallback conditions.

    Returns None when the report is too small (fewer than
    min_cluster_size * 2 embeddings) or when more than 80% of points are
    labeled as noise.
    """
    if len(embeddings) < min_cluster_size * 2:
        return None

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        cluster_selection_method="leaf",
    )
    labels = clusterer.fit_predict(embeddings).astype(np.int32)

    noise_count = int(np.sum(labels == -1))
    noise_ratio = noise_count / len(labels)
    if noise_ratio > 0.8:
        return None

    unique_labels = set(labels.tolist())
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

    return ClusterResult(
        labels=labels,
        n_clusters=n_clusters,
        n_noise=noise_count,
        is_fallback=False,
    )
