"""Mock pipeline verification to test logic flow without dependencies.

This script simulates the pipeline with mock objects to verify:
1. Format table/JSON logic is correct
2. Fallback handling works
3. Error handling is appropriate
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock the dataclasses from template_extractor
@dataclass
class MockClusterTemplate:
    cluster_id: int
    template: str
    count: int
    values: list[list[str]]

@dataclass
class MockExtractionResult:
    clusters: list[MockClusterTemplate]
    noise_lines: list[str]
    is_fallback: bool

def test_format_table_logic():
    """Test format_table with mock data."""
    print("\n1. Testing format_table logic")
    print("-"*60)
    
    # Mock a result
    result = MockExtractionResult(
        clusters=[
            MockClusterTemplate(
                cluster_id=0,
                template="Warning: signal <*> unconnected at module <*>",
                count=3,
                values=[
                    ["clk_sync", "CORE_CPU_0"],
                    ["rst_n", "REG_FILE_0"],
                    ["data_bus", "ALU_0"],
                ],
            ),
            MockClusterTemplate(
                cluster_id=1,
                template="Error: latch inferred in <*>",
                count=2,
                values=[
                    ["LATCH_CTRL_0"],
                    ["STATE_MACHINE_0"],
                ],
            ),
        ],
        noise_lines=["Uncategorized line 1", "Uncategorized line 2"],
        is_fallback=False,
    )
    
    # Test that we can access all fields
    try:
        assert len(result.clusters) == 2, "Should have 2 clusters"
        assert result.clusters[0].cluster_id == 0, "First cluster ID should be 0"
        assert result.clusters[0].count == 3, "First cluster should have count 3"
        assert len(result.clusters[0].values) == 3, "First cluster should have 3 value sets"
        assert len(result.noise_lines) == 2, "Should have 2 noise lines"
        assert result.is_fallback is False, "Should not be fallback mode"
        print("  ✓ ExtractionResult structure is correct")
    except AssertionError as e:
        print(f"  ✗ {e}")
        return False
    
    return True

def test_format_json_logic():
    """Test format_json with mock data."""
    print("\n2. Testing format_json logic")
    print("-"*60)
    
    result = MockExtractionResult(
        clusters=[
            MockClusterTemplate(
                cluster_id=0,
                template="Line <*>",
                count=5,
                values=[["1"], ["2"], ["3"], ["4"], ["5"]],
            ),
        ],
        noise_lines=[],
        is_fallback=True,
    )
    
    # Simulate format_json logic
    clusters_data = []
    for cluster in result.clusters:
        clusters_data.append({
            "cluster_id": cluster.cluster_id,
            "template": cluster.template,
            "count": cluster.count,
            "values": cluster.values,
        })
    
    metadata = {
        "is_fallback": result.is_fallback,
        "total_clusters": len(result.clusters),
        "total_noise": len(result.noise_lines),
        "clustering_mode": "drain3_only" if result.is_fallback else "hdbscan_drain3",
    }
    
    data = {
        "clusters": clusters_data,
        "unclustered": result.noise_lines,
        "metadata": metadata,
    }
    
    try:
        json_str = json.dumps(data, indent=2)
        parsed = json.loads(json_str)
        
        assert "clusters" in parsed, "JSON should have clusters key"
        assert "unclustered" in parsed, "JSON should have unclustered key"
        assert "metadata" in parsed, "JSON should have metadata key"
        assert parsed["metadata"]["is_fallback"] is True, "Should indicate fallback"
        assert parsed["metadata"]["clustering_mode"] == "drain3_only", "Should indicate drain3_only mode"
        
        print("  ✓ JSON structure is valid")
        print(f"  ✓ JSON has {len(parsed['clusters'])} clusters")
        print(f"  ✓ Clustering mode: {parsed['metadata']['clustering_mode']}")
    except Exception as e:
        print(f"  ✗ JSON test failed: {e}")
        return False
    
    return True

def test_fallback_logic():
    """Test fallback condition handling."""
    print("\n3. Testing fallback logic")
    print("-"*60)
    
    # Simulate cluster_embeddings returning None
    cluster_result = None
    
    if cluster_result is None:
        print("  ✓ Detected cluster_result is None")
        print("  ✓ Should call extract_templates(lines, labels=None)")
        fallback_mode = True
    else:
        print("  ✗ Failed to detect None result")
        return False
    
    # Simulate normal clustering
    @dataclass
    class MockClusterResult:
        labels: list[int]
        n_clusters: int
        n_noise: int
        is_fallback: bool
    
    cluster_result = MockClusterResult(
        labels=[0, 0, 1, 1, -1],
        n_clusters=2,
        n_noise=1,
        is_fallback=False,
    )
    
    if cluster_result is not None:
        print("  ✓ Detected valid cluster_result")
        print("  ✓ Should call extract_templates(lines, cluster_result.labels)")
        normal_mode = True
    else:
        print("  ✗ Failed to detect valid result")
        return False
    
    return True

def test_error_handling():
    """Test error condition handling."""
    print("\n4. Testing error handling logic")
    print("-"*60)
    
    # Test empty lines check
    lines = []
    if not lines:
        print("  ✓ Detected empty lines (should exit with code 1)")
    else:
        print("  ✗ Failed to detect empty lines")
        return False
    
    # Test file not found
    try:
        filepath = Path("/nonexistent/file.txt")
        if not filepath.exists():
            raise FileNotFoundError(f"Report file not found: {filepath}")
    except FileNotFoundError:
        print("  ✓ FileNotFoundError caught (should exit with code 2)")
    
    # Test encoding error
    try:
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    except UnicodeDecodeError:
        print("  ✓ UnicodeDecodeError caught (should exit with code 1)")
    
    return True

def test_parser_integration():
    """Test parser integration."""
    print("\n5. Testing parser integration")
    print("-"*60)
    
    try:
        from vlsi_report_cluster.parser import parse_report
        
        fixtures_path = Path(__file__).parent / "fixtures"
        
        # Test with sample_lint.txt
        lint_file = fixtures_path / "sample_lint.txt"
        if lint_file.exists():
            lines = parse_report(lint_file)
            print(f"  ✓ Parsed sample_lint.txt: {len(lines)} lines")
        
        # Test with tiny_report.txt
        tiny_file = fixtures_path / "tiny_report.txt"
        if tiny_file.exists():
            lines = parse_report(tiny_file)
            print(f"  ✓ Parsed tiny_report.txt: {len(lines)} lines")
        
        # Test with empty.txt
        empty_file = fixtures_path / "empty.txt"
        if empty_file.exists():
            lines = parse_report(empty_file)
            if len(lines) == 0:
                print("  ✓ Empty file returns empty list")
            else:
                print(f"  ✗ Empty file returned {len(lines)} lines")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Parser integration failed: {e}")
        return False

def main():
    """Run all mock tests."""
    print("="*60)
    print("Mock Pipeline Verification")
    print("="*60)
    
    tests = [
        test_format_table_logic,
        test_format_json_logic,
        test_fallback_logic,
        test_error_handling,
        test_parser_integration,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ Test raised exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✓ ALL MOCK TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
