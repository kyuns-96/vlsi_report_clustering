"""Tests for embedder module using TDD approach."""

import os
import numpy as np
import pytest
from vlsi_report_cluster.embedder import (
    Embedder,
    LocalEmbedder,
    OpenAIEmbedder,
    create_embedder,
)


# Test 1: Protocol compliance - both implementations should satisfy Protocol
def test_embedder_protocol_compliance():
    """Test that LocalEmbedder and OpenAIEmbedder satisfy Embedder protocol."""
    local = LocalEmbedder()
    assert hasattr(local, "embed")
    assert callable(local.embed)
    
    # Only test OpenAI if API key is available
    if os.environ.get("OPENAI_API_KEY"):
        openai_embedder = OpenAIEmbedder()
        assert hasattr(openai_embedder, "embed")
        assert callable(openai_embedder.embed)


# Test 2: LocalEmbedder returns numpy array
def test_local_embedder_returns_numpy_array():
    """Test LocalEmbedder returns numpy array for list of strings."""
    embedder = LocalEmbedder()
    lines = ["Warning: signal CLK unconnected", "Error: latch inferred for DATA"]
    result = embedder.embed(lines)
    
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 2  # 2 input lines


# Test 3: LocalEmbedder produces 384 dimensions (for all-MiniLM-L6-v2)
def test_local_embedder_dimensions():
    """Test LocalEmbedder output dimension is 384."""
    embedder = LocalEmbedder()
    lines = ["Warning: signal CLK unconnected"]
    result = embedder.embed(lines)
    
    assert result.shape == (1, 384)


# Test 4: Empty input handling
def test_embedder_empty_input():
    """Test embedder handles empty input list."""
    embedder = LocalEmbedder()
    result = embedder.embed([])
    
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 0


# Test 5: Similar lines have high cosine similarity (> 0.7)
def test_local_embedder_similar_lines_close():
    """Test semantically similar lines have high cosine similarity."""
    embedder = LocalEmbedder()
    lines = [
        "Warning: signal CLK is unconnected at module CPU",
        "Warning: signal RST is unconnected at module GPU",
    ]
    vecs = embedder.embed(lines)
    
    # Compute cosine similarity
    vec0_norm = vecs[0] / np.linalg.norm(vecs[0])
    vec1_norm = vecs[1] / np.linalg.norm(vecs[1])
    similarity = np.dot(vec0_norm, vec1_norm)
    
    assert similarity > 0.7, f"Similar lines should have similarity > 0.7, got {similarity}"


# Test 6: Different lines have lower cosine similarity (< 0.5)
def test_local_embedder_different_lines_far():
    """Test semantically different lines have lower cosine similarity."""
    embedder = LocalEmbedder()
    lines = [
        "Warning: signal CLK is unconnected at module CPU",
        "Error: latch inferred for signal DATA in module MEM",
    ]
    vecs = embedder.embed(lines)
    
    # Compute cosine similarity
    vec0_norm = vecs[0] / np.linalg.norm(vecs[0])
    vec1_norm = vecs[1] / np.linalg.norm(vecs[1])
    similarity = np.dot(vec0_norm, vec1_norm)
    
    assert similarity < 0.5, f"Different lines should have similarity < 0.5, got {similarity}"


# Test 7: OpenAI embedder returns numpy array (skip if no API key)
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
def test_openai_embedder_returns_numpy_array():
    """Test OpenAIEmbedder returns numpy array for list of strings."""
    embedder = OpenAIEmbedder()
    lines = ["Warning: signal CLK unconnected"]
    result = embedder.embed(lines)
    
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 1


# Test 8: Factory function returns LocalEmbedder
def test_create_embedder_local():
    """Test create_embedder factory returns LocalEmbedder for backend='local'."""
    embedder = create_embedder("local")
    assert isinstance(embedder, LocalEmbedder)


# Test 9: Factory function returns OpenAIEmbedder (skip if no API key)
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
def test_create_embedder_openai():
    """Test create_embedder factory returns OpenAIEmbedder for backend='openai'."""
    embedder = create_embedder("openai")
    assert isinstance(embedder, OpenAIEmbedder)
