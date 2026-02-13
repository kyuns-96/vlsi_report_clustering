# VLSI Report Cluster

A powerful tool for analyzing and clustering VLSI verification reports using machine learning and log template mining. Automatically groups similar violations, errors, and warnings to help you understand report patterns at scale.

## Features

- **Multi-Format Support**: Parse text, HTML, and CSV report formats
- **Semantic Clustering**: Uses sentence-transformers to group semantically similar violations
- **Template Extraction**: Automatically extracts log templates with wildcard patterns using Drain3
- **Fallback Handling**: Gracefully handles small reports or high-noise scenarios
- **Configurable OpenAI Endpoint**: Set custom OpenAI-compatible API base URL via JSON config file
- **Rich Output**: Beautiful terminal tables or JSON for programmatic access
- **Production Ready**: Comprehensive error handling and edge case support

## Installation

### Basic Installation

```bash
pip install -e .
```

### With OpenAI Embedding Support

If you prefer using OpenAI's embeddings instead of local models:

```bash
pip install -e ".[openai]"
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or store OpenAI settings in a config file and pass `--config` (see below).

### Development Installation

For running tests and development:

```bash
pip install -e ".[dev]"
```

### First-Run Model Download

**Note**: On first run, the tool will download the `all-MiniLM-L6-v2` sentence-transformers model (~90MB). This is a one-time download and will be cached locally.

## Usage

### Basic Usage (Text Report)

```bash
vlsi-report-cluster report.txt
```

Output:
```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Cluster ┃ Template                                ┃ Count ┃ Sample Values          ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 0       │ Warning: signal <*> unconnected at <*>  │ 15    │ clk_sync, rst_n, ...   │
│ 1       │ Error: latch inferred in <*> (net: <*>) │ 8     │ CORE_CPU_0, MEM_CTRL_1 │
└─────────┴─────────────────────────────────────────┴───────┴────────────────────────┘
```

### HTML Report with JSON Output

```bash
vlsi-report-cluster report.html --output-format json
```

Output:
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "template": "Warning: signal <*> unconnected at <*>",
      "count": 15,
      "values": [["clk_sync", "CORE_CPU_0/BUFFER_0"], ...]
    }
  ],
  "unclustered": ["Line without pattern"],
  "metadata": {
    "total_clusters": 1,
    "total_lines": 16,
    "is_fallback": false
  }
}
```

### Custom Clustering Parameters

Fine-tune HDBSCAN clustering:

```bash
vlsi-report-cluster report.txt --min-cluster-size 5 --min-samples 3
```

### Different File Encoding

If your report uses non-UTF-8 encoding:

```bash
vlsi-report-cluster report.txt --encoding latin-1
```

### Override Format Detection

Force a specific parser:

```bash
vlsi-report-cluster report.dat --format text
```

### Use OpenAI Embeddings

```bash
vlsi-report-cluster report.txt --embedder openai --embedder-model text-embedding-3-small
```

### Configure OpenAI API Location via Config File

Create a JSON config file:

```json
{
  "openai": {
    "api_key": "your-api-key-here",
    "base_url": "http://localhost:8080/v1"
  }
}
```

Then run:

```bash
vlsi-report-cluster report.txt --embedder openai --config config.json
```

If `openai.api_key` is set in config, you do not need `OPENAI_API_KEY` in the environment.

## CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `report_file` | Path | **Required** | Input report file path |
| `--output-format` | str | `table` | Output format: `table` or `json` |
| `--format` | str | Auto-detect | Override format detection: `text`, `html`, or `csv` |
| `--config` | Path | None | Path to JSON config file (supports `openai.api_key`, `openai.base_url`) |
| `--min-cluster-size` | int | `3` | HDBSCAN minimum cluster size (higher = fewer, larger clusters) |
| `--min-samples` | int | `2` | HDBSCAN minimum samples (higher = stricter clustering) |
| `--embedder` | str | `local` | Embedding backend: `local` or `openai` |
| `--embedder-model` | str | Auto | Custom model name (local: sentence-transformers models, openai: ada-002, text-embedding-3-small, etc.) |
| `--encoding` | str | `utf-8` | File encoding (try `latin-1`, `cp1252` if UTF-8 fails) |

## Output Formats

### Table Format (Default)

Human-readable Rich terminal table with:
- **Cluster ID**: Unique identifier for each cluster
- **Template**: Log template with `<*>` wildcards for variable parts
- **Count**: Number of lines matching this template
- **Sample Values**: Preview of extracted variable values

Includes an "Unclustered" section for lines that didn't fit any cluster (noise).

### JSON Format

Machine-readable JSON with:
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "template": "...",
      "count": 10,
      "values": [[...], ...]
    }
  ],
  "unclustered": ["line1", "line2"],
  "metadata": {
    "total_clusters": 3,
    "total_lines": 50,
    "is_fallback": false
  }
}
```

## Architecture

```
[Report File] → [Parser] → [Lines]
                               ↓
                          [Embedder] → [Vectors (384-dim or 1536-dim)]
                               ↓
                        [HDBSCAN Clusterer] → [Labels or None]
                               ↓
                    [Template Extractor (Drain3)] → [Templates]
                               ↓
                    [Formatter (Rich/JSON)] → [Output]
```

### Pipeline Details

1. **Parser** (`parser.py`)
   - Auto-detects format from file extension (`.txt`, `.html`, `.csv`)
   - Extracts and filters lines (removes separators, empty lines, short lines)
   - Supports custom encoding for non-UTF-8 files

2. **Embedder** (`embedder.py`)
   - Converts text lines to semantic vector embeddings
   - **Local**: Uses `sentence-transformers` (384-dim vectors, offline, free)
   - **OpenAI**: Uses OpenAI API (1536-dim vectors, requires API key)

3. **Clusterer** (`clusterer.py`)
   - HDBSCAN density-based clustering
   - Groups semantically similar lines
   - **Fallback**: Returns `None` for small reports or high noise (triggers Drain3-only mode)

4. **Template Extractor** (`template_extractor.py`)
   - Drain3 log template mining
   - Extracts patterns with `<*>` wildcards for variable parts
   - **Normal mode**: Applies templates within each cluster
   - **Fallback mode**: Applies templates to all lines (no clustering)

5. **Formatter** (`formatter.py`)
   - Rich terminal tables (colorized, aligned)
   - JSON output (for scripts and automation)

## Supported Report Formats

### Plain Text (.txt, .rpt, .log)

Line-by-line text reports:
```
Warning: signal clk_sync unconnected at module CORE_CPU_0
Error: latch inferred in MEM_CTRL_1/STATE_MACHINE_0
```

### HTML (.html, .htm)

HTML reports with tables or text:
```html
<html>
  <body>
    <table>
      <tr><td>Warning</td><td>signal unconnected</td></tr>
    </table>
  </body>
</html>
```

### CSV (.csv)

CSV reports with violation data:
```csv
severity,message,module
Warning,signal clk_sync unconnected,CORE_CPU_0
Error,latch inferred,MEM_CTRL_1
```

## Fallback Behavior

When HDBSCAN clustering is not effective (small reports, high noise), the tool automatically falls back to **Drain3-only mode**:

- **Trigger conditions**:
  - Fewer than 10 lines in report
  - More than 70% of lines classified as noise by HDBSCAN
  - Manual trigger: `clusterer.py` returns `None`

- **Behavior**:
  - Applies Drain3 template mining directly to all lines
  - All lines assigned to templates (no "unclustered" section)
  - `is_fallback: true` in metadata

## Error Handling

The tool handles errors gracefully with user-friendly messages:

- **File not found**: `Error: File not found: <path>`
- **Encoding errors**: `Error: Unable to decode file. Try --encoding parameter`
- **Missing dependencies**: `Error: Missing dependency: <module>. Install with: pip install vlsi-report-cluster`
- **Empty reports**: `Error: No lines found in report`

All errors are printed to stderr in red using Rich console formatting. No Python tracebacks are shown to users.

## Examples

### Analyze a Lint Report

```bash
vlsi-report-cluster tests/fixtures/sample_lint.txt
```

### Analyze Power Intent Violations

```bash
vlsi-report-cluster tests/fixtures/sample_power_intent.txt --min-cluster-size 4
```

### Export Results to JSON for Processing

```bash
vlsi-report-cluster report.txt --output-format json > results.json
python analyze_results.py results.json
```

### Handle Non-UTF-8 Reports

```bash
vlsi-report-cluster legacy_report.txt --encoding latin-1
```

## Dependencies

Core dependencies:
- **typer**: CLI framework
- **rich**: Terminal formatting and tables
- **sentence-transformers**: Local embedding models
- **hdbscan**: Density-based clustering
- **drain3**: Log template mining
- **beautifulsoup4**: HTML parsing
- **numpy**: Numerical operations

Optional dependencies:
- **openai**: OpenAI API client (for `--embedder openai`)
- **pytest**: Testing framework (dev only)

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test modules:

```bash
pytest tests/test_edge_cases.py -v
pytest tests/test_parser.py -v
pytest tests/test_cli.py -v
```

Manual test runner (when pytest is unavailable):

```bash
python tests/test_edge_cases.py
python tests/test_parser.py
python tests/test_cli.py
```

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
- Tests pass: `pytest tests/ -v`
- Code is formatted: `ruff format .`
- Type hints are added where appropriate

## Troubleshooting

### Model Download Fails

If the sentence-transformers model download fails:
1. Check internet connection
2. Try downloading manually:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```

### Unicode Errors

Try different encodings:
```bash
vlsi-report-cluster report.txt --encoding latin-1
vlsi-report-cluster report.txt --encoding cp1252
```

### Empty Results

If clustering produces no results:
- **Report too small**: The tool will automatically use fallback mode
- **All lines filtered**: Check if lines are too short (min 5 chars) or only separators
- **Adjust parameters**: Try `--min-cluster-size 2 --min-samples 1`

### High Noise

If too many lines are "unclustered":
- **Lower min-cluster-size**: Try `--min-cluster-size 2`
- **Use fallback mode**: The tool will automatically trigger for high noise
- **Check report quality**: Are violations structured consistently?

## Development

### Project Structure

```
vlsi_report_cluster/
├── src/vlsi_report_cluster/
│   ├── cli.py                 # CLI interface and pipeline
│   ├── parser.py              # Multi-format parser
│   ├── embedder.py            # Embedding backends
│   ├── clusterer.py           # HDBSCAN clustering
│   ├── template_extractor.py  # Drain3 template mining
│   └── formatter.py           # Output formatting
├── tests/
│   ├── fixtures/              # Test report files
│   ├── test_parser.py         # Parser tests
│   ├── test_cli.py            # CLI integration tests
│   └── test_edge_cases.py     # Edge case tests
├── pyproject.toml             # Package configuration
└── README.md                  # This file
```

### Adding New Parsers

To add support for a new report format:

1. Add format detection in `parser.py`:
   ```python
   def detect_format(filepath: Path, override: str | None = None) -> str:
       if override == "newformat":
           return "newformat"
       # ...
   ```

2. Implement parser function:
   ```python
   def parse_newformat(filepath: Path, encoding: str) -> list[str]:
       # Parse and return lines
       pass
   ```

3. Add to `parse_report()`:
   ```python
   if format == "newformat":
       return parse_newformat(filepath, encoding)
   ```

### Adding New Embedders

To add a new embedding backend:

1. Create embedder class in `embedder.py`:
   ```python
   class NewEmbedder(Embedder):
       def embed(self, texts: list[str]) -> np.ndarray:
           # Implement embedding logic
           pass
   ```

2. Register in `create_embedder()`:
   ```python
   if backend == "new":
       return NewEmbedder(model)
   ```

## Changelog

### v0.1.0 (Initial Release)

- Multi-format parser (text, HTML, CSV)
- Local embedding with sentence-transformers
- OpenAI embedding support
- HDBSCAN clustering with fallback
- Drain3 template extraction
- Rich table and JSON output
- Comprehensive error handling
- Edge case tests (unicode, long lines, identical lines, etc.)
