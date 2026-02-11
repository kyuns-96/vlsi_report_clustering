"""Tests for the report parser module."""

from pathlib import Path
import pytest
from vlsi_report_cluster.parser import detect_format, parse_report


class TestFormatDetection:
    """Tests for format detection logic."""

    def test_detect_format_text(self):
        """Test that .txt, .rpt, .log extensions are detected as 'text' format."""
        assert detect_format(Path("report.txt")) == "text"
        assert detect_format(Path("report.rpt")) == "text"
        assert detect_format(Path("report.log")) == "text"
        assert detect_format(Path("/some/path/file.txt")) == "text"

    def test_detect_format_html(self):
        """Test that .html, .htm extensions are detected as 'html' format."""
        assert detect_format(Path("report.html")) == "html"
        assert detect_format(Path("report.htm")) == "html"
        assert detect_format(Path("/some/path/file.html")) == "html"

    def test_detect_format_csv(self):
        """Test that .csv extension is detected as 'csv' format."""
        assert detect_format(Path("report.csv")) == "csv"
        assert detect_format(Path("/some/path/file.csv")) == "csv"

    def test_detect_format_override(self):
        """Test that override parameter forces format detection."""
        # Override should take precedence over extension
        assert detect_format(Path("report.xyz"), override="text") == "text"
        assert detect_format(Path("report.html"), override="csv") == "csv"
        assert detect_format(Path("report.txt"), override="html") == "html"

    def test_detect_format_unknown(self):
        """Test that unknown extensions raise ValueError."""
        with pytest.raises(ValueError, match="Unknown file format"):
            detect_format(Path("report.xyz"))


class TestLineFiltering:
    """Tests for line filtering logic."""

    def test_filter_separator_lines(self, tmp_path):
        """Test that separator lines (---, ===, ***) are filtered out."""
        test_file = tmp_path / "test.txt"
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
        # Only valid lines should remain
        assert len(lines) == 5
        assert "Valid line 1" in lines
        assert "Valid line 5" in lines
        # Separator lines should be removed
        assert not any("---" in line for line in lines)
        assert not any("===" in line for line in lines)
        assert not any("***" in line for line in lines)

    def test_filter_empty_lines(self, tmp_path):
        """Test that empty lines are filtered out."""
        test_file = tmp_path / "test.txt"
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

    def test_filter_short_lines(self, tmp_path):
        """Test that lines shorter than min_line_length are filtered out."""
        test_file = tmp_path / "test.txt"
        test_file.write_text(
            "This is a long enough line\n"
            "abc\n"
            "x\n"
            "Another valid line here\n"
            "12\n"
        )
        # Default min_line_length is 5
        lines = parse_report(test_file, min_line_length=5)
        assert len(lines) == 2
        assert "This is a long enough line" in lines
        assert "Another valid line here" in lines
        # Short lines should be filtered
        assert "abc" not in lines
        assert "x" not in lines

    def test_filter_custom_min_length(self, tmp_path):
        """Test that custom min_line_length parameter works."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("abc\ndefgh\nxyz123\n")
        # With min_length=6, only "xyz123" should pass
        lines = parse_report(test_file, min_line_length=6)
        assert len(lines) == 1
        assert "xyz123" in lines


class TestTextParsing:
    """Tests for plain text report parsing."""

    def test_parse_text_report(self, fixtures_path):
        """Test parsing a plain text VLSI report."""
        test_file = fixtures_path / "sample_lint.txt"
        lines = parse_report(test_file)
        
        # Should have violation lines (not headers, separators, or empty lines)
        assert len(lines) > 0
        assert all(len(line) >= 5 for line in lines)
        
        # Verify some expected content is present
        assert any("Warning" in line for line in lines)
        assert any("Error" in line for line in lines)
        
        # Headers and separators should be filtered
        assert not any("====" in line for line in lines)
        assert not any("Generated:" in line for line in lines)

    def test_parse_tiny_report(self, fixtures_path):
        """Test parsing a minimal report."""
        test_file = fixtures_path / "tiny_report.txt"
        lines = parse_report(test_file)
        
        assert len(lines) > 0
        assert all(len(line) >= 5 for line in lines)

    def test_parse_empty_report(self, fixtures_path):
        """Test parsing an empty report returns empty list."""
        test_file = fixtures_path / "empty.txt"
        lines = parse_report(test_file)
        assert lines == []


class TestHTMLParsing:
    """Tests for HTML report parsing."""

    def test_parse_html_report(self, fixtures_path):
        """Test parsing an HTML VLSI report."""
        test_file = fixtures_path / "sample_report.html"
        lines = parse_report(test_file)
        
        # Should extract visible text lines
        assert len(lines) > 0
        assert all(len(line) >= 5 for line in lines)
        
        # Should contain data from table
        assert any("Warning" in line for line in lines)
        assert any("Error" in line for line in lines)
        
        # HTML tags should not be present
        assert not any("<" in line and ">" in line for line in lines)

    def test_parse_html_extracts_text_only(self, tmp_path):
        """Test that HTML parsing extracts only visible text."""
        test_file = tmp_path / "test.html"
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


class TestCSVParsing:
    """Tests for CSV report parsing."""

    def test_parse_csv_report(self, fixtures_path):
        """Test parsing a CSV VLSI report."""
        test_file = fixtures_path / "sample_report.csv"
        lines = parse_report(test_file)
        
        # Should have concatenated rows
        assert len(lines) > 0
        
        # Each line should be a concatenated row
        # CSV format: severity,rule_id,message,file,line
        assert any("Warning" in line for line in lines)
        assert any("Error" in line for line in lines)
        
        # Should contain module names from the file column
        assert any("CORE_CPU_0" in line for line in lines)

    def test_parse_csv_concatenates_fields(self, tmp_path):
        """Test that CSV parsing concatenates all fields in each row."""
        test_file = tmp_path / "test.csv"
        test_file.write_text(
            "severity,message,module\n"
            "Warning,signal unconnected,CORE_CPU_0\n"
            "Error,latch inferred,MEM_CTRL_1\n"
        )
        lines = parse_report(test_file)
        
        # Should have 2 data rows (header filtered or included depending on implementation)
        assert len(lines) >= 2
        
        # Each line should contain concatenated fields
        # At least one line should have all fields from a data row
        assert any("Warning" in line and "signal unconnected" in line and "CORE_CPU_0" in line for line in lines)


class TestParseReportIntegration:
    """Integration tests for the main parse_report function."""

    def test_parse_report_auto_detects_format(self, fixtures_path):
        """Test that parse_report auto-detects format from extension."""
        # Text file
        text_lines = parse_report(fixtures_path / "sample_lint.txt")
        assert len(text_lines) > 0
        
        # HTML file
        html_lines = parse_report(fixtures_path / "sample_report.html")
        assert len(html_lines) > 0
        
        # CSV file
        csv_lines = parse_report(fixtures_path / "sample_report.csv")
        assert len(csv_lines) > 0

    def test_parse_report_with_format_override(self, tmp_path):
        """Test that parse_report respects format parameter."""
        # Create a .xyz file with text content
        test_file = tmp_path / "test.xyz"
        test_file.write_text("Valid line 1\nValid line 2\n")
        
        # Should work with format override
        lines = parse_report(test_file, format="text")
        assert len(lines) == 2
        assert "Valid line 1" in lines

    def test_parse_report_with_encoding(self, tmp_path):
        """Test that parse_report respects encoding parameter."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line with special chars: café", encoding="utf-8")
        
        lines = parse_report(test_file, encoding="utf-8")
        assert len(lines) == 1
        assert "café" in lines[0]

    def test_parse_report_all_fixtures(self, fixtures_path):
        """Test that parser works on all fixture files without errors."""
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
            # Should not raise any exceptions
            lines = parse_report(filepath)
            # Result should always be a list
            assert isinstance(lines, list)
            # All lines should be strings
            assert all(isinstance(line, str) for line in lines)
