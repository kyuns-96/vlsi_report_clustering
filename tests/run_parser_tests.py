#!/usr/bin/env python3
"""Manual test runner for parser module (pytest not available)."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vlsi_report_cluster.parser import detect_format, parse_report


def test_detect_format_text():
    """Test that .txt, .rpt, .log extensions are detected as 'text' format."""
    assert detect_format(Path("report.txt")) == "text"
    assert detect_format(Path("report.rpt")) == "text"
    assert detect_format(Path("report.log")) == "text"
    assert detect_format(Path("/some/path/file.txt")) == "text"


def test_detect_format_html():
    """Test that .html, .htm extensions are detected as 'html' format."""
    assert detect_format(Path("report.html")) == "html"
    assert detect_format(Path("report.htm")) == "html"
    assert detect_format(Path("/some/path/file.html")) == "html"


def test_detect_format_csv():
    """Test that .csv extension is detected as 'csv' format."""
    assert detect_format(Path("report.csv")) == "csv"
    assert detect_format(Path("/some/path/file.csv")) == "csv"


def test_detect_format_override():
    """Test that override parameter forces format detection."""
    assert detect_format(Path("report.xyz"), override="text") == "text"
    assert detect_format(Path("report.html"), override="csv") == "csv"
    assert detect_format(Path("report.txt"), override="html") == "html"


def test_detect_format_unknown():
    """Test that unknown extensions raise ValueError."""
    try:
        detect_format(Path("report.xyz"))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown file format" in str(e)


def test_filter_separator_lines():
    """Test that separator lines (---, ===, ***) are filtered out."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text(
            "Valid line 1\n"
            "---\n"
            "Valid line 2\n"
            "===\n"
            "Valid line 3\n"
            "***\n"
            "Valid line 4\n"
            "--------------------\n"
            "Valid line 5\n"
        )
        lines = parse_report(test_file)
        assert len(lines) == 5
        assert "Valid line 1" in lines
        assert "Valid line 5" in lines
        assert not any("---" in line for line in lines)
        assert not any("===" in line for line in lines)
        assert not any("***" in line for line in lines)


def test_filter_empty_lines():
    """Test that empty lines are filtered out."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text(
            "Valid line 1\n"
            "\n"
            "Valid line 2\n"
            "   \n"
            "Valid line 3\n"
        )
        lines = parse_report(test_file)
        assert len(lines) == 3
        assert "Valid line 1" in lines
        assert "Valid line 3" in lines


def test_filter_short_lines():
    """Test that lines shorter than min_line_length are filtered out."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text(
            "This is a long enough line\n"
            "abc\n"
            "x\n"
            "Another valid line here\n"
            "12\n"
        )
        lines = parse_report(test_file, min_line_length=5)
        assert len(lines) == 2
        assert "This is a long enough line" in lines
        assert "Another valid line here" in lines
        assert "abc" not in lines
        assert "x" not in lines


def test_filter_custom_min_length():
    """Test that custom min_line_length parameter works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("abc\ndefgh\nxyz123\n")
        lines = parse_report(test_file, min_line_length=6)
        assert len(lines) == 1
        assert "xyz123" in lines


def test_parse_text_report():
    """Test parsing a plain text VLSI report."""
    fixtures_path = Path(__file__).parent / "fixtures"
    test_file = fixtures_path / "sample_lint.txt"
    lines = parse_report(test_file)
    
    assert len(lines) > 0
    assert all(len(line) >= 5 for line in lines)
    
    # Verify some expected content is present
    assert any("Warning" in line for line in lines)
    assert any("Error" in line for line in lines)
    
    # Separator lines should be filtered
    assert not any("====" in line for line in lines)


def test_parse_tiny_report():
    """Test parsing a minimal report."""
    fixtures_path = Path(__file__).parent / "fixtures"
    test_file = fixtures_path / "tiny_report.txt"
    lines = parse_report(test_file)
    
    assert len(lines) > 0
    assert all(len(line) >= 5 for line in lines)


def test_parse_empty_report():
    """Test parsing an empty report returns empty list."""
    fixtures_path = Path(__file__).parent / "fixtures"
    test_file = fixtures_path / "empty.txt"
    lines = parse_report(test_file)
    assert lines == []


def test_parse_html_report():
    """Test parsing an HTML VLSI report."""
    fixtures_path = Path(__file__).parent / "fixtures"
    test_file = fixtures_path / "sample_report.html"
    lines = parse_report(test_file)
    
    assert len(lines) > 0
    assert all(len(line) >= 5 for line in lines)
    
    # Should contain data from table
    assert any("Warning" in line for line in lines)
    assert any("Error" in line for line in lines)
    
    # HTML tags should not be present
    assert not any("<" in line and ">" in line for line in lines)


def test_parse_html_extracts_text_only():
    """Test that HTML parsing extracts only visible text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.html"
        test_file.write_text(
            "<html><body>"
            "<p>Line 1 visible</p>"
            "<div>Line 2 visible</div>"
            "<script>var x = 'not visible';</script>"
            "</body></html>"
        )
        lines = parse_report(test_file)
        
        # Should have visible text
        assert any("Line 1 visible" in line for line in lines)
        assert any("Line 2 visible" in line for line in lines)
        
        # Script content should not appear
        assert not any("not visible" in line for line in lines)


def test_parse_csv_report():
    """Test parsing a CSV VLSI report."""
    fixtures_path = Path(__file__).parent / "fixtures"
    test_file = fixtures_path / "sample_report.csv"
    lines = parse_report(test_file)
    
    assert len(lines) > 0
    
    # Each line should be a concatenated row
    assert any("Warning" in line for line in lines)
    assert any("Error" in line for line in lines)
    
    # Should contain module names from the file column
    assert any("CORE_CPU_0" in line for line in lines)


def test_parse_csv_concatenates_fields():
    """Test that CSV parsing concatenates all fields in each row."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.csv"
        test_file.write_text(
            "severity,message,module\n"
            "Warning,signal unconnected,CORE_CPU_0\n"
            "Error,latch inferred,MEM_CTRL_1\n"
        )
        lines = parse_report(test_file)
        
        assert len(lines) >= 2
        
        # Each line should contain concatenated fields
        assert any("Warning" in line and "signal unconnected" in line and "CORE_CPU_0" in line for line in lines)


def test_parse_report_auto_detects_format():
    """Test that parse_report auto-detects format from extension."""
    fixtures_path = Path(__file__).parent / "fixtures"
    
    # Text file
    text_lines = parse_report(fixtures_path / "sample_lint.txt")
    assert len(text_lines) > 0
    
    # HTML file
    html_lines = parse_report(fixtures_path / "sample_report.html")
    assert len(html_lines) > 0
    
    # CSV file
    csv_lines = parse_report(fixtures_path / "sample_report.csv")
    assert len(csv_lines) > 0


def test_parse_report_with_format_override():
    """Test that parse_report respects format parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.xyz"
        test_file.write_text("Valid line 1\nValid line 2\n")
        
        lines = parse_report(test_file, format="text")
        assert len(lines) == 2
        assert "Valid line 1" in lines


def test_parse_report_with_encoding():
    """Test that parse_report respects encoding parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Line with special chars: café", encoding="utf-8")
        
        lines = parse_report(test_file, encoding="utf-8")
        assert len(lines) == 1
        assert "café" in lines[0]


def test_parse_report_all_fixtures():
    """Test that parser works on all fixture files without errors."""
    fixtures_path = Path(__file__).parent / "fixtures"
    fixtures = [
        "sample_lint.txt",
        "tiny_report.txt",
        "sample_report.html",
        "sample_report.csv",
        "empty.txt",
        "sample_power_intent.txt"
    ]
    
    for fixture_name in fixtures:
        filepath = fixtures_path / fixture_name
        lines = parse_report(filepath)
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)


def run_tests():
    """Run all tests and report results."""
    tests = [
        ("Format Detection - text", test_detect_format_text),
        ("Format Detection - html", test_detect_format_html),
        ("Format Detection - csv", test_detect_format_csv),
        ("Format Detection - override", test_detect_format_override),
        ("Format Detection - unknown", test_detect_format_unknown),
        ("Filter - separator lines", test_filter_separator_lines),
        ("Filter - empty lines", test_filter_empty_lines),
        ("Filter - short lines", test_filter_short_lines),
        ("Filter - custom min length", test_filter_custom_min_length),
        ("Parse - text report", test_parse_text_report),
        ("Parse - tiny report", test_parse_tiny_report),
        ("Parse - empty report", test_parse_empty_report),
        ("Parse - html report", test_parse_html_report),
        ("Parse - html text only", test_parse_html_extracts_text_only),
        ("Parse - csv report", test_parse_csv_report),
        ("Parse - csv concatenates", test_parse_csv_concatenates_fields),
        ("Integration - auto detect", test_parse_report_auto_detects_format),
        ("Integration - format override", test_parse_report_with_format_override),
        ("Integration - encoding", test_parse_report_with_encoding),
        ("Integration - all fixtures", test_parse_report_all_fixtures),
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 70)
    print("Running Parser Module Tests")
    print("=" * 70)
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
