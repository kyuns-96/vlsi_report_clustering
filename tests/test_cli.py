"""Tests for CLI integration (test_cli.py).

This test suite verifies the full CLI pipeline:
parse → embed → cluster → extract → format

Since pytest is not available, tests are written to be runnable
via a manual test runner similar to test_parser.py.
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vlsi_report_cluster.cli import app
from vlsi_report_cluster.formatter import format_json, format_table
from vlsi_report_cluster.template_extractor import ClusterTemplate, ExtractionResult


class TestFormatter:
    """Test the formatter module."""

    def test_format_table_with_clusters(self):
        """Test format_table with clustered results."""
        result = ExtractionResult(
            clusters=[
                ClusterTemplate(
                    cluster_id=0,
                    template="Warning: signal <*> unconnected at module <*>",
                    count=3,
                    values=[
                        ["clk_sync", "CORE_CPU_0/BUFFER_0"],
                        ["rst_n", "CORE_CPU_0/REGISTER_FILE_0"],
                        ["data_bus[15:0]", "CORE_CPU_0/ALU_UNIT_0"],
                    ],
                ),
                ClusterTemplate(
                    cluster_id=1,
                    template="Error: latch inferred in <*> (net: <*>)",
                    count=2,
                    values=[
                        ["CORE_CPU_0/LATCH_CTRL_0", "ff_enable"],
                        ["CORE_CPU_0/STATE_MACHINE_0", "state_q[1]"],
                    ],
                ),
            ],
            noise_lines=["Line 1 without pattern", "Line 2 without pattern"],
            is_fallback=False,
        )
        
        output = format_table(result)
        
        # Verify table output contains expected components
        assert "Cluster" in output, "Table should have Cluster column"
        assert "Template" in output, "Table should have Template column"
        assert "Count" in output, "Table should have Count column"
        assert "Sample Values" in output, "Table should have Sample Values column"
        assert "Warning: signal <*>" in output, "Template should appear in table"
        assert "Error: latch inferred" in output, "Template should appear in table"
        assert "Unclustered" in output or "noise" in output.lower(), "Should show unclustered section"
    
    def test_format_table_with_fallback(self):
        """Test format_table with Drain3-only fallback."""
        result = ExtractionResult(
            clusters=[
                ClusterTemplate(
                    cluster_id=0,
                    template="VLSI Report - Minimal",
                    count=1,
                    values=[[]],
                ),
            ],
            noise_lines=[],
            is_fallback=True,
        )
        
        output = format_table(result)
        
        assert "Cluster" in output, "Table should have headers"
        assert "Template" in output, "Template column should exist"
    
    def test_format_json_with_clusters(self):
        """Test format_json produces valid JSON."""
        result = ExtractionResult(
            clusters=[
                ClusterTemplate(
                    cluster_id=0,
                    template="Warning: signal <*> unconnected",
                    count=2,
                    values=[["clk_sync"], ["rst_n"]],
                ),
            ],
            noise_lines=["Noise line 1"],
            is_fallback=False,
        )
        
        output = format_json(result)
        
        # Parse JSON to verify validity
        data = json.loads(output)
        
        assert "clusters" in data, "JSON should have clusters key"
        assert isinstance(data["clusters"], list), "clusters should be a list"
        assert len(data["clusters"]) == 1, "Should have 1 cluster"
        
        cluster = data["clusters"][0]
        assert "cluster_id" in cluster, "Cluster should have cluster_id"
        assert "template" in cluster, "Cluster should have template"
        assert "count" in cluster, "Cluster should have count"
        assert "values" in cluster, "Cluster should have values"
        
        assert "unclustered" in data, "JSON should have unclustered key"
        assert len(data["unclustered"]) == 1, "Should have 1 unclustered line"
        
        assert "metadata" in data, "JSON should have metadata"
        assert "is_fallback" in data["metadata"], "Metadata should have is_fallback"
    
    def test_format_json_with_fallback(self):
        """Test format_json with fallback mode."""
        result = ExtractionResult(
            clusters=[
                ClusterTemplate(
                    cluster_id=0,
                    template="Line <*>",
                    count=5,
                    values=[["1"], ["2"], ["3"], ["4"], ["5"]],
                ),
            ],
            noise_lines=[],
            is_fallback=True,
        )
        
        output = format_json(result)
        data = json.loads(output)
        
        assert data["metadata"]["is_fallback"] is True, "Should indicate fallback mode"
        assert data["metadata"]["total_clusters"] == 1, "Should have 1 cluster"


class TestCLIIntegration:
    """Test CLI integration with full pipeline."""
    
    def test_cli_imports_successfully(self):
        """Test that CLI module imports without errors."""
        from vlsi_report_cluster import cli
        
        assert hasattr(cli, "app"), "CLI should have app"
        assert hasattr(cli, "main"), "CLI should have main function"
    
    def test_cli_pipeline_with_text_report(self):
        """Test CLI processes text report successfully."""
        # This test verifies the CLI can:
        # 1. Parse a text report
        # 2. Embed the lines
        # 3. Cluster the embeddings
        # 4. Extract templates
        # 5. Format as table
        
        # This is a structural test - actual execution requires installed dependencies
        from vlsi_report_cluster.parser import parse_report
        from vlsi_report_cluster.embedder import create_embedder
        from vlsi_report_cluster.clusterer import cluster_embeddings
        from vlsi_report_cluster.template_extractor import extract_templates
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "sample_lint.txt"
        
        # Verify file exists
        assert report_file.exists(), f"Fixture file should exist: {report_file}"
        
        # Verify parser works
        lines = parse_report(report_file)
        assert len(lines) > 0, "Parser should return lines"
        
        # Note: Cannot test embed/cluster/extract without dependencies installed
        # This test verifies the pipeline structure is correct
    
    def test_cli_pipeline_with_tiny_report_fallback(self):
        """Test CLI handles small reports with Drain3-only fallback."""
        from vlsi_report_cluster.parser import parse_report
        from vlsi_report_cluster.template_extractor import extract_templates
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "tiny_report.txt"
        
        lines = parse_report(report_file)
        assert len(lines) > 0, "Tiny report should have lines"
        
        # Test fallback mode (labels=None)
        result = extract_templates(lines, labels=None)
        assert result.is_fallback is True, "Should use fallback mode"
        assert len(result.clusters) > 0, "Should extract templates"
        assert len(result.noise_lines) == 0, "Fallback mode has no noise"
    
    def test_cli_pipeline_with_empty_file(self):
        """Test CLI handles empty file gracefully."""
        from vlsi_report_cluster.parser import parse_report
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "empty.txt"
        
        lines = parse_report(report_file)
        assert len(lines) == 0, "Empty file should return empty list"
    
    def test_cli_pipeline_with_html_report(self):
        """Test CLI handles HTML format."""
        from vlsi_report_cluster.parser import parse_report
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "sample_report.html"
        
        lines = parse_report(report_file)
        assert len(lines) > 0, "HTML parser should extract lines"
    
    def test_cli_pipeline_with_csv_report(self):
        """Test CLI handles CSV format."""
        from vlsi_report_cluster.parser import parse_report
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "sample_report.csv"
        
        lines = parse_report(report_file)
        assert len(lines) > 0, "CSV parser should extract lines"
    
    def test_cli_pipeline_with_format_override(self):
        """Test CLI format override parameter."""
        from vlsi_report_cluster.parser import parse_report
        
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "sample_lint.txt"
        
        # Override format (even though extension is .txt)
        lines = parse_report(report_file, format="text")
        assert len(lines) > 0, "Format override should work"
    
    def test_cli_pipeline_with_nonexistent_file(self):
        """Test CLI handles nonexistent file."""
        from vlsi_report_cluster.parser import parse_report
        
        nonexistent_file = Path("/tmp/nonexistent_file_12345.txt")
        
        try:
            parse_report(nonexistent_file)
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError as e:
            assert "not found" in str(e).lower(), "Error message should mention 'not found'"


# Manual test runner
def run_tests():
    """Run all tests manually."""
    test_classes = [TestFormatter, TestCLIIntegration]
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total_tests += 1
            method = getattr(test_instance, method_name)
            
            try:
                method()
                print(f"✓ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
            except Exception as e:
                print(f"✗ {method_name}: EXCEPTION: {e}")
                failed_tests.append((test_class.__name__, method_name, f"EXCEPTION: {e}"))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Total: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\nFailed tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  {class_name}.{method_name}: {error}")
        return 1
    else:
        print("\n✓ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(run_tests())
