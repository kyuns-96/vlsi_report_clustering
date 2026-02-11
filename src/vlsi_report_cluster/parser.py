"""Report parser module.

This module provides functionality to parse VLSI report files in multiple formats
(text, HTML, CSV) and extract violation lines for clustering analysis.
"""

import csv
import re
from pathlib import Path
from typing import Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore


def detect_format(filepath: Path, override: Optional[str] = None) -> str:
    """Detect report format from file extension.
    
    Args:
        filepath: Path to the report file
        override: Optional format override ('text', 'html', or 'csv')
        
    Returns:
        Format string: 'text', 'html', or 'csv'
        
    Raises:
        ValueError: If file format cannot be determined
    """
    if override:
        return override
    
    # Map extensions to formats
    extension = filepath.suffix.lower()
    format_map = {
        ".txt": "text",
        ".rpt": "text",
        ".log": "text",
        ".html": "html",
        ".htm": "html",
        ".csv": "csv",
    }
    
    if extension not in format_map:
        raise ValueError(
            f"Unknown file format: {extension}. "
            f"Supported: {', '.join(format_map.keys())}. "
            f"Use --format to override."
        )
    
    return format_map[extension]


def _filter_lines(lines: list[str], min_length: int) -> list[str]:
    """Filter out separator lines, empty lines, and short lines.
    
    Args:
        lines: List of lines to filter
        min_length: Minimum line length to keep
        
    Returns:
        Filtered list of lines
    """
    # Separator patterns to remove
    separator_patterns = [
        r"^-+$",  # Lines with only dashes
        r"^=+$",  # Lines with only equals
        r"^\*+$",  # Lines with only asterisks
    ]
    
    filtered = []
    for line in lines:
        # Strip whitespace
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Skip short lines
        if len(stripped) < min_length:
            continue
        
        # Skip separator lines
        is_separator = any(re.match(pattern, stripped) for pattern in separator_patterns)
        if is_separator:
            continue
        
        filtered.append(stripped)
    
    return filtered


def _parse_text(filepath: Path, encoding: str) -> list[str]:
    """Parse a plain text report file.
    
    Args:
        filepath: Path to the text file
        encoding: Character encoding
        
    Returns:
        List of lines from the file
    """
    with open(filepath, "r", encoding=encoding) as f:
        return f.readlines()


def _parse_html(filepath: Path, encoding: str) -> list[str]:
    """Parse an HTML report file and extract visible text.
    
    Args:
        filepath: Path to the HTML file
        encoding: Character encoding
        
    Returns:
        List of text lines extracted from HTML
        
    Raises:
        ImportError: If BeautifulSoup4 is not installed
    """
    if BeautifulSoup is None:
        raise ImportError(
            "BeautifulSoup4 is required for HTML parsing. "
            "Install with: pip install beautifulsoup4"
        )
    
    with open(filepath, "r", encoding=encoding) as f:
        content = f.read()
    
    soup = BeautifulSoup(content, "html.parser")
    
    # Extract visible text, using newlines as separators
    text = soup.get_text(separator="\n")
    
    # Split into lines
    return text.split("\n")


def _parse_csv(filepath: Path, encoding: str) -> list[str]:
    """Parse a CSV report file and concatenate fields into lines.
    
    Args:
        filepath: Path to the CSV file
        encoding: Character encoding
        
    Returns:
        List of lines, each containing concatenated CSV fields
    """
    lines = []
    
    with open(filepath, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            # Concatenate all fields with spaces
            line = " ".join(field.strip() for field in row if field.strip())
            if line:
                lines.append(line)
    
    return lines


def parse_report(
    filepath: Path,
    format: Optional[str] = None,
    encoding: str = "utf-8",
    min_line_length: int = 5,
) -> list[str]:
    """Parse a VLSI report file and extract violation lines.
    
    This is the main entry point for report parsing. It auto-detects the format
    from the file extension (or uses the override), parses the file using the
    appropriate parser, and filters out separators, headers, and short lines.
    
    Args:
        filepath: Path to the report file
        format: Optional format override ('text', 'html', or 'csv')
        encoding: Character encoding (default: utf-8)
        min_line_length: Minimum line length to keep (default: 5)
        
    Returns:
        List of filtered violation lines
        
    Raises:
        ValueError: If file format cannot be determined
        FileNotFoundError: If file does not exist
        ImportError: If required parser library is missing
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Report file not found: {filepath}")
    
    # Detect format
    detected_format = detect_format(filepath, override=format)
    
    # Parse using appropriate parser
    if detected_format == "text":
        raw_lines = _parse_text(filepath, encoding)
    elif detected_format == "html":
        raw_lines = _parse_html(filepath, encoding)
    elif detected_format == "csv":
        raw_lines = _parse_csv(filepath, encoding)
    else:
        raise ValueError(f"Unsupported format: {detected_format}")
    
    # Filter lines
    filtered_lines = _filter_lines(raw_lines, min_line_length)
    
    return filtered_lines
