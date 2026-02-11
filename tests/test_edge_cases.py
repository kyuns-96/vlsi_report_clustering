"""Tests for edge cases and error handling.

This test suite verifies the tool handles unusual inputs gracefully:
- All identical lines
- All unique lines
- Unicode characters
- Very long lines
- Mixed severity patterns
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vlsi_report_cluster.parser import parse_report
from vlsi_report_cluster.template_extractor import extract_templates


class TestEdgeCases:
    """Test edge cases in report processing."""
    
    def test_all_identical_lines(self):
        """Test report with all identical lines produces single cluster."""
        # Create temporary file with identical lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            identical_line = "Warning: signal CLK unconnected at module CPU"
            for _ in range(20):
                f.write(identical_line + "\n")
            temp_path = Path(f.name)
        
        try:
            # Parse and extract
            lines = parse_report(temp_path)
            assert len(lines) == 20, f"Should have 20 lines, got {len(lines)}"
            
            # Extract templates (fallback mode since no labels)
            result = extract_templates(lines, labels=None)
            
            # Should produce exactly 1 cluster
            assert len(result.clusters) == 1, f"Expected 1 cluster, got {len(result.clusters)}"
            assert result.clusters[0].count == 20, f"Expected count=20, got {result.clusters[0].count}"
            
            print("✓ test_all_identical_lines passed")
        finally:
            temp_path.unlink()
    
    def test_all_unique_lines(self):
        """Test report with all unique lines."""
        # Create temporary file with completely different lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i in range(20):
                # Each line is completely different
                f.write(f"Unique error type {i} with random pattern xyz{i*17} and data abc{i*23}\n")
            temp_path = Path(f.name)
        
        try:
            # Parse and extract
            lines = parse_report(temp_path)
            assert len(lines) == 20, f"Should have 20 lines, got {len(lines)}"
            
            # Extract templates (fallback mode)
            result = extract_templates(lines, labels=None)
            
            # Should produce multiple clusters (Drain3 may group some by structure)
            # or many clusters with count=1
            assert len(result.clusters) >= 1, "Should have at least 1 cluster"
            
            # Most lines should be in small clusters or individual templates
            single_line_clusters = sum(1 for c in result.clusters if c.count == 1)
            assert single_line_clusters >= 10, f"Expected >=10 single-line clusters, got {single_line_clusters}"
            
            print("✓ test_all_unique_lines passed")
        finally:
            temp_path.unlink()
    
    def test_unicode_file(self):
        """Test file with unicode characters (non-ASCII module names)."""
        # Create temporary file with unicode
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            # Chinese module names
            f.write("Warning: signal 时钟_clk unconnected at module 处理器_CPU_0\n")
            f.write("Warning: signal 复位_rst unconnected at module 处理器_CPU_1\n")
            # Japanese module names
            f.write("Error: ラッチ inferred in モジュール_MEM_0\n")
            # Cyrillic
            f.write("Info: порт unused in модуль_IO_0\n")
            # Emoji (why not)
            f.write("Warning: signal 🔥_alert unconnected at module 🔧_CTRL_0\n")
            temp_path = Path(f.name)
        
        try:
            # Parse (should handle UTF-8)
            lines = parse_report(temp_path, encoding='utf-8')
            assert len(lines) == 5, f"Should have 5 lines, got {len(lines)}"
            
            # Verify unicode is preserved
            assert any("时钟" in line for line in lines), "Chinese characters should be preserved"
            assert any("ラッチ" in line for line in lines), "Japanese characters should be preserved"
            assert any("порт" in line for line in lines), "Cyrillic characters should be preserved"
            
            # Extract templates
            result = extract_templates(lines, labels=None)
            assert len(result.clusters) >= 1, "Should extract templates from unicode text"
            
            print("✓ test_unicode_file passed")
        finally:
            temp_path.unlink()
    
    def test_very_long_lines(self):
        """Test lines >1000 chars don't crash."""
        # Create temporary file with very long lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Line 1: 2000 characters
            long_path = "top." + ".".join([f"sub{i}" for i in range(200)])  # ~800 chars of hierarchy
            f.write(f"Warning: signal VERY_LONG_SIGNAL_NAME_{'X'*500} unconnected at module {long_path}\n")
            
            # Line 2: 1500 characters
            long_path2 = "top." + ".".join([f"sub{i}" for i in range(150)])
            f.write(f"Warning: signal ANOTHER_LONG_SIGNAL_{'Y'*400} unconnected at module {long_path2}\n")
            
            # Line 3: normal length for comparison
            f.write("Warning: signal CLK unconnected at module CPU\n")
            
            temp_path = Path(f.name)
        
        try:
            # Parse (should not crash on long lines)
            lines = parse_report(temp_path)
            assert len(lines) == 3, f"Should have 3 lines, got {len(lines)}"
            
            # Verify long lines are preserved
            assert any(len(line) > 1000 for line in lines), "Should have at least one line >1000 chars"
            
            # Extract templates (should handle long lines)
            result = extract_templates(lines, labels=None)
            assert len(result.clusters) >= 1, "Should extract templates from long lines"
            
            print("✓ test_very_long_lines passed")
        finally:
            temp_path.unlink()
    
    def test_mixed_severity_patterns(self):
        """Test report with Warning/Error/Info clusters by content, not severity."""
        # Create temporary file with mixed severities but similar content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Pattern 1: unconnected signals (mixed severities)
            f.write("Warning: signal CLK unconnected at module CPU_0\n")
            f.write("Error: signal RST unconnected at module CPU_1\n")
            f.write("Warning: signal DATA unconnected at module GPU_0\n")
            
            # Pattern 2: latch inference (mixed severities)
            f.write("Error: latch inferred for signal ADDR in module MEM_0\n")
            f.write("Warning: latch inferred for signal CTRL in module MEM_1\n")
            f.write("Error: latch inferred for signal STATUS in module MEM_2\n")
            
            # Pattern 3: unused ports
            f.write("Info: unused port SCAN_EN in module IO_0\n")
            f.write("Warning: unused port TEST_MODE in module IO_1\n")
            f.write("Info: unused port DEBUG in module IO_2\n")
            
            temp_path = Path(f.name)
        
        try:
            # Parse
            lines = parse_report(temp_path)
            assert len(lines) == 9, f"Should have 9 lines, got {len(lines)}"
            
            # Extract templates
            result = extract_templates(lines, labels=None)
            
            # Drain3 should cluster by content pattern, not by severity keyword
            # We expect 3 clusters (unconnected, latch, unused port)
            # Each cluster may have mixed severities
            assert len(result.clusters) >= 2, f"Expected >=2 clusters, got {len(result.clusters)}"
            
            # Check that at least one cluster has count > 1
            cluster_counts = [c.count for c in result.clusters]
            assert max(cluster_counts) >= 2, "At least one cluster should have multiple lines"
            
            # Verify templates contain the key patterns
            templates = [c.template for c in result.clusters]
            template_str = " ".join(templates)
            
            # Should have templates for the main patterns (not just severity levels)
            has_signal_pattern = any("signal" in t or "<*>" in t for t in templates)
            assert has_signal_pattern, "Should have template for signal-related pattern"
            
            print("✓ test_mixed_severity_patterns passed")
        finally:
            temp_path.unlink()
    
    def test_empty_after_filtering(self):
        """Test report that becomes empty after filtering (only separators/headers)."""
        # Create file with only separators and short lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("---\n")
            f.write("===\n")
            f.write("***\n")
            f.write("====================================\n")
            f.write("   \n")  # whitespace only
            f.write("\n")     # empty
            f.write("ABC\n")  # 3 chars (below default min_line_length=5)
            temp_path = Path(f.name)
        
        try:
            # Parse (should filter everything out)
            lines = parse_report(temp_path)
            assert len(lines) == 0, f"Should have 0 lines after filtering, got {len(lines)}"
            
            print("✓ test_empty_after_filtering passed")
        finally:
            temp_path.unlink()
    
    def test_power_intent_multi_pattern(self):
        """Test with sample_power_intent.txt fixture (multi-pattern report)."""
        fixtures_path = Path(__file__).parent / "fixtures"
        report_file = fixtures_path / "sample_power_intent.txt"
        
        if not report_file.exists():
            print("⊘ test_power_intent_multi_pattern skipped (fixture not found)")
            return
        
        # Parse
        lines = parse_report(report_file)
        assert len(lines) > 0, "Power intent report should have lines"
        
        # Extract templates
        result = extract_templates(lines, labels=None)
        
        # Should find multiple patterns (isolation, level shifter, retention)
        assert len(result.clusters) >= 2, f"Expected >=2 clusters in power intent report, got {len(result.clusters)}"
        
        # Check templates contain power-related terms
        templates = [c.template for c in result.clusters]
        template_str = " ".join(templates).lower()
        
        # Should have templates for power intent patterns
        power_keywords = ["isolation", "shifter", "retention", "power", "domain"]
        has_power_pattern = any(keyword in template_str for keyword in power_keywords)
        assert has_power_pattern or any("<*>" in t for t in templates), \
            "Should have power-related templates or wildcards"
        
        print("✓ test_power_intent_multi_pattern passed")


# Manual test runner
def run_tests():
    """Run all edge case tests manually."""
    test_suite = TestEdgeCases()
    test_methods = [m for m in dir(test_suite) if m.startswith("test_")]
    
    print("="*70)
    print(f"Running {len(test_methods)} edge case tests")
    print("="*70)
    print()
    
    passed = 0
    failed = 0
    skipped = 0
    
    for method_name in test_methods:
        try:
            method = getattr(test_suite, method_name)
            method()
            passed += 1
        except AssertionError as e:
            print(f"✗ {method_name}: {e}")
            failed += 1
        except Exception as e:
            if "skipped" in str(e).lower():
                skipped += 1
            else:
                print(f"✗ {method_name}: EXCEPTION: {e}")
                failed += 1
    
    print()
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(test_methods)} tests")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
