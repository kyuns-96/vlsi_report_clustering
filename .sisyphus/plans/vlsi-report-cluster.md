# VLSI Report Cluster — Work Plan

## TL;DR

> **Quick Summary**: Build a Python CLI tool that takes a single VLSI sanity check report file, clusters semantically similar violation lines using AI embeddings + HDBSCAN, extracts templates per cluster via Drain3, and outputs grouped results (template + count + extracted values) to the terminal or JSON.
> 
> **Deliverables**:
> - Python CLI tool `vlsi-report-cluster` installable via pip
> - Pluggable embedding engine (local sentence-transformers default, OpenAI optional)
> - HDBSCAN clustering with small-report fallback to Drain3-only mode
> - Rich terminal output + JSON output option
> - Full TDD test suite with synthetic fixtures
> 
> **Estimated Effort**: Medium (5-7 days)
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Task 1 (project setup) → Task 2 (parser) → Task 4 (embedder) → Task 5 (clusterer) → Task 6 (template extractor) → Task 7 (CLI integration) → Task 8 (edge cases)

---

## Context

### Original Request
Build a VLSI report parsing and clustering tool. The user works with sanity check reports (VSLP, GCA, Lint, Formal, Power Intent) that contain many similar violation/check lines. The goal is to cluster similar lines within a single report to reduce review effort.

### Interview Summary
**Key Discussions**:
- **Report types**: VSLP, GCA, Lint, Formal, Power Intent — industry standard sanity check reports
- **Scope**: Cluster lines WITHIN a single report file (not across reports)
- **Format**: Reports come in mixed formats (text, HTML, CSV) — parser must be generic, not report-type-specific
- **Output**: CLI tool showing Template + occurrence count + extracted variable values
- **No sample reports**: Build generic/flexible — no real samples available for testing
- **Clustering method**: User specifically wants AI embedding approach (not pure regex/Drain3)
- **Architecture**: Embed → HDBSCAN → Drain3 post-clustering pipeline

**Research Findings**:
- **No existing tools**: GitHub has zero mature VLSI report clustering tools — this is novel
- **Drain3** (logpai/Drain3, MIT, 747 stars): Production-ready log template mining. Originally designed for full pipeline, but excellent as post-clustering template extractor
- **sentence-transformers**: `all-MiniLM-L6-v2` (384-dim, ~90MB) is fast and runs on CPU
- **HDBSCAN**: Density-based clustering that auto-detects cluster count and identifies noise/outliers

### Metis Review
**Identified Gaps** (addressed):
- **Small report fallback**: If report has <10 lines or HDBSCAN marks >80% as noise, skip embedding/clustering and use Drain3-only mode
- **Noise point handling**: HDBSCAN label=-1 points must be shown as "Unclustered" section
- **Drain3 state isolation**: MUST create fresh `TemplateMiner()` per HDBSCAN cluster — Drain3 is stateful
- **Line definition for HTML/CSV**: Define extraction strategy per format (text→newline split, HTML→`get_text()`, CSV→row concatenation)
- **Synthetic test fixtures**: Since no real reports available, create 3-4 fixture files mimicking VLSI report patterns
- **Output format**: Default rich terminal table + `--output-format json` option
- **Encoding**: UTF-8 default with `--encoding` CLI flag (no auto-detect)

---

## Work Objectives

### Core Objective
Build a stateless Python CLI tool that parses a VLSI sanity check report, clusters semantically similar lines using AI embeddings + HDBSCAN, extracts templates per cluster using Drain3, and outputs results as grouped templates with counts and values.

### Concrete Deliverables
- `vlsi_report_cluster/` Python package with src layout
- `pyproject.toml` with CLI entry point
- 5 pipeline modules: `parser`, `embedder`, `clusterer`, `template_extractor`, `formatter`
- CLI entry point via `typer`
- Test suite with synthetic VLSI report fixtures
- `README.md` with usage instructions

### Definition of Done
- [ ] `pip install -e .` succeeds
- [ ] `vlsi-report-cluster sample_report.txt` produces clustered output with templates
- [ ] `vlsi-report-cluster sample_report.txt --output-format json` produces valid JSON
- [ ] `vlsi-report-cluster tiny_report.txt` (5 lines) falls back gracefully
- [ ] `vlsi-report-cluster report.html` auto-detects HTML format
- [ ] `pytest tests/ -v` — all tests pass
- [ ] `vlsi-report-cluster --embedder openai report.txt` works with API key set

### Must Have
- Generic line-based parsing (text, HTML, CSV format detection)
- AI embedding with pluggable model (local default + OpenAI)
- HDBSCAN clustering with automatic cluster detection
- Drain3 template extraction per cluster with `<*>` wildcards
- Noise point handling (unclustered lines shown separately)
- Small report fallback (Drain3-only when HDBSCAN fails)
- JSON output option
- TDD test suite

### Must NOT Have (Guardrails)
- NO report-type-specific parsing logic (no `if report_type == "VSLP"` branches)
- NO visualization (no matplotlib, no charts, no dendrograms)
- NO persistent state between runs (no database, no cache)
- NO cross-report comparison
- NO interactive mode
- NO web UI
- NO custom Drain3 masking for VLSI patterns (v1)
- NO auto-encoding detection (UTF-8 default, `--encoding` flag)
- NO async/concurrent processing
- NO plugin system for embedders — two concrete implementations behind a Protocol
- NO fine-tuning or model training — inference only with pre-trained models
- NO export formats beyond stdout/JSON (no Excel, PDF, etc.)

---

## Verification Strategy

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: NO (greenfield project)
- **Automated tests**: TDD (RED-GREEN-REFACTOR)
- **Framework**: pytest

### Test Infrastructure Setup (Task 1)
- pytest + pytest-cov
- `tests/` directory with `conftest.py`
- Synthetic fixture files in `tests/fixtures/`
- `pyproject.toml` with `[tool.pytest.ini_options]`

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

Every task includes QA scenarios using Bash (pytest, CLI invocation).

**Verification Tool by Deliverable Type:**

| Type | Tool | How Agent Verifies |
|------|------|-------------------|
| **Python package** | Bash (pip, python -c) | Install, import, call functions |
| **CLI tool** | Bash (command invocation) | Run with args, assert stdout/stderr/exit code |
| **Test suite** | Bash (pytest) | Run tests, assert all pass |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: Project scaffolding + test infrastructure
└── Task 3: Create synthetic test fixtures

Wave 2 (After Wave 1):
├── Task 2: Report parser module (format detection + line extraction)
├── Task 4: Embedder module (Protocol + local + OpenAI implementations)
└── (Task 3 fixtures available for Tasks 2, 4)

Wave 3 (After Wave 2):
├── Task 5: Clusterer module (HDBSCAN + small-report fallback)
└── Task 6: Template extractor module (Drain3 per cluster)

Wave 4 (After Wave 3):
├── Task 7: CLI integration (Typer + Rich output + JSON)
└── Task 8: Edge cases + error handling + README

Critical Path: Task 1 → Task 2 → Task 5 → Task 6 → Task 7
Parallel Speedup: ~35% faster than sequential
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2, 3, 4 | 3 |
| 2 | 1 | 5, 7 | 4 |
| 3 | 1 | 2, 4, 5, 6 | 1 (partial) |
| 4 | 1 | 5, 7 | 2 |
| 5 | 2, 4 | 6, 7 | 6 (partial) |
| 6 | 5 | 7 | — |
| 7 | 2, 4, 5, 6 | 8 | — |
| 8 | 7 | None | — |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 3 | task(category="quick", ...) — scaffolding and fixture creation |
| 2 | 2, 4 | task(category="unspecified-high", ...) — module implementation with TDD |
| 3 | 5, 6 | task(category="ultrabrain", ...) — clustering + template extraction logic |
| 4 | 7, 8 | task(category="unspecified-high", ...) — CLI integration + hardening |

---

## TODOs

- [x] 1. Project Scaffolding + Test Infrastructure

  **What to do**:
  - Create Python project with src layout:
    ```
    vlsi_report_cluster/
    ├── pyproject.toml
    ├── src/
    │   └── vlsi_report_cluster/
    │       ├── __init__.py
    │       ├── __main__.py
    │       ├── cli.py
    │       ├── parser.py
    │       ├── embedder.py
    │       ├── clusterer.py
    │       ├── template_extractor.py
    │       └── formatter.py
    ├── tests/
    │   ├── conftest.py
    │   ├── fixtures/
    │   └── test_parser.py (placeholder)
    └── README.md
    ```
  - Create `pyproject.toml` with:
    - Project metadata (name=`vlsi-report-cluster`, version=`0.1.0`)
    - Dependencies: `typer>=0.9.0`, `rich>=10.11.0`, `sentence-transformers>=2.2.0`, `hdbscan>=0.8.33`, `drain3>=0.9.11`, `beautifulsoup4>=4.12.0`, `numpy>=1.24.0`
    - Dev dependencies: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `ruff>=0.1.0`
    - Optional `openai` extra: `openai>=1.0.0`
    - CLI entry point: `[project.scripts] vlsi-report-cluster = "vlsi_report_cluster.cli:app"`
    - pytest config: `[tool.pytest.ini_options] testpaths = ["tests"]`
  - Create empty module files with docstrings
  - Create `tests/conftest.py` with path fixture for `tests/fixtures/`
  - Run `pip install -e ".[dev]"` to verify installation
  - Run `pytest tests/ -v` to verify test infrastructure works (0 tests collected is OK)

  **Must NOT do**:
  - Do NOT implement any logic in modules — just create files with docstrings/pass
  - Do NOT install OpenAI dependency by default
  - Do NOT add linting/formatting CI pipeline

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure scaffolding — creating files and directories, no complex logic
  - **Skills**: []
    - No specialized skills needed for project setup
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI work
    - `git-master`: No git operations required yet

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 3)
  - **Blocks**: Tasks 2, 3, 4
  - **Blocked By**: None (can start immediately)

  **References**:

  **External References**:
  - Typer docs: https://typer.tiangolo.com/ — CLI framework setup and entry points
  - Python packaging guide: https://packaging.python.org/en/latest/tutorials/packaging-projects/ — pyproject.toml best practices
  - sentence-transformers: https://www.sbert.net/docs/installation.html — dependency version constraints

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Project installs successfully
    Tool: Bash
    Preconditions: Python 3.10+ available
    Steps:
      1. cd /home/lee/workspace/vlsi_report_cluster
      2. pip install -e ".[dev]" 2>&1
      3. Assert: exit code 0
      4. python -c "import vlsi_report_cluster; print('OK')"
      5. Assert: stdout contains "OK"
    Expected Result: Package installs and imports without error
    Evidence: Command output captured

  Scenario: CLI entry point registered
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. vlsi-report-cluster --help
      2. Assert: exit code 0
      3. Assert: stdout contains "Usage" or "--help"
    Expected Result: CLI help text displayed
    Evidence: Command output captured

  Scenario: Test infrastructure works
    Tool: Bash
    Preconditions: Package installed with dev deps
    Steps:
      1. pytest tests/ -v 2>&1
      2. Assert: exit code 0 (even with 0 tests)
      3. Assert: stdout contains "passed" or "no tests ran"
    Expected Result: pytest runs without error
    Evidence: Command output captured
  ```

  **Commit**: YES
  - Message: `feat(init): scaffold project with pyproject.toml, src layout, and test infrastructure`
  - Files: `pyproject.toml`, `src/vlsi_report_cluster/*.py`, `tests/conftest.py`
  - Pre-commit: `pip install -e ".[dev]" && pytest tests/ -v`

---

- [x] 2. Report Parser Module (Format Detection + Line Extraction)

  **What to do**:
  - **RED**: Write tests first in `tests/test_parser.py`:
    - `test_parse_text_report()` — given a plain text file, returns list of non-empty, non-separator lines
    - `test_parse_html_report()` — given an HTML file, extracts visible text lines
    - `test_parse_csv_report()` — given a CSV file, concatenates each row's fields into a single line
    - `test_detect_format_text()` — `.txt`, `.rpt`, `.log` → `"text"`
    - `test_detect_format_html()` — `.html`, `.htm` → `"html"`
    - `test_detect_format_csv()` — `.csv` → `"csv"`
    - `test_detect_format_override()` — `--format text` overrides extension-based detection
    - `test_filter_separator_lines()` — lines like `---`, `===`, `***` are removed
    - `test_filter_empty_lines()` — blank lines removed
    - `test_filter_short_lines()` — lines < 5 chars removed (configurable threshold)
  - **GREEN**: Implement `src/vlsi_report_cluster/parser.py`:
    - `detect_format(filepath: Path, override: str | None = None) -> str` — returns "text", "html", or "csv"
    - `parse_report(filepath: Path, format: str | None = None, encoding: str = "utf-8", min_line_length: int = 5) -> list[str]` — main entry point
    - `_parse_text(filepath, encoding) -> list[str]` — read file, split by newlines
    - `_parse_html(filepath, encoding) -> list[str]` — BeautifulSoup `get_text(separator='\n')`, then split
    - `_parse_csv(filepath, encoding) -> list[str]` — csv.reader, concatenate fields with spaces
    - `_filter_lines(lines, min_length) -> list[str]` — remove empty, separator, and short lines
  - **REFACTOR**: Clean up, add type hints, docstrings

  **Must NOT do**:
  - Do NOT add report-type-specific parsing (no VSLP/GCA/Lint-specific logic)
  - Do NOT add encoding auto-detection
  - Do NOT try to parse table structure within reports
  - Do NOT handle binary files (just raise clear error)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Core module with TDD, needs careful design but not algorithmic complexity
  - **Skills**: []
    - Standard Python module — no specialized skills needed
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI
    - `playwright`: No browser testing

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 4)
  - **Blocks**: Tasks 5, 7
  - **Blocked By**: Task 1 (project scaffold), Task 3 (test fixtures)

  **References**:

  **External References**:
  - BeautifulSoup4 docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/ — `get_text()` with separator parameter
  - Python csv module: https://docs.python.org/3/library/csv.html — `csv.reader` for CSV parsing
  - Python pathlib: https://docs.python.org/3/library/pathlib.html — `Path.suffix` for format detection

  **Pattern References**:
  - Test fixtures created in Task 3 at `tests/fixtures/` — use these for all parser tests

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_parser.py`
  - [ ] Tests cover: format detection, text/HTML/CSV parsing, line filtering
  - [ ] `pytest tests/test_parser.py -v` → PASS (10+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Parse a text report
    Tool: Bash
    Preconditions: Package installed, tests/fixtures/sample_lint.txt exists
    Steps:
      1. python -c "
         from vlsi_report_cluster.parser import parse_report
         from pathlib import Path
         lines = parse_report(Path('tests/fixtures/sample_lint.txt'))
         print(f'Lines: {len(lines)}')
         for l in lines[:3]: print(repr(l))
         "
      2. Assert: Lines count > 0
      3. Assert: No empty strings in output
      4. Assert: No separator lines (---, ===) in output
    Expected Result: Clean list of violation/content lines
    Evidence: Command output captured

  Scenario: Parse an HTML report
    Tool: Bash
    Preconditions: tests/fixtures/sample_report.html exists
    Steps:
      1. python -c "
         from vlsi_report_cluster.parser import parse_report
         from pathlib import Path
         lines = parse_report(Path('tests/fixtures/sample_report.html'))
         print(f'Lines: {len(lines)}')
         assert len(lines) > 0
         assert all(len(l) >= 5 for l in lines)
         print('OK')
         "
      2. Assert: stdout contains "OK"
    Expected Result: Text extracted from HTML, filtered
    Evidence: Command output captured

  Scenario: Format detection works
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. python -c "
         from vlsi_report_cluster.parser import detect_format
         from pathlib import Path
         assert detect_format(Path('report.txt')) == 'text'
         assert detect_format(Path('report.rpt')) == 'text'
         assert detect_format(Path('report.html')) == 'html'
         assert detect_format(Path('report.csv')) == 'csv'
         assert detect_format(Path('report.xyz'), override='text') == 'text'
         print('All format detection OK')
         "
      2. Assert: stdout contains "All format detection OK"
    Expected Result: All format detection assertions pass
    Evidence: Command output captured
  ```

  **Commit**: YES
  - Message: `feat(parser): add report parser with format detection and line extraction`
  - Files: `src/vlsi_report_cluster/parser.py`, `tests/test_parser.py`
  - Pre-commit: `pytest tests/test_parser.py -v`

---

- [x] 3. Create Synthetic Test Fixtures

  **What to do**:
  - Create `tests/fixtures/` directory with the following synthetic VLSI report files:
  - **`sample_lint.txt`** (~50-60 lines): Simulates a lint/sanity check report with:
    - Header section (tool name, date, version — 5-6 lines)
    - Separator lines (`===`, `---`)
    - ~15 "Warning: signal X is unconnected at module Y line Z" violations (same template, different values)
    - ~10 "Error: latch inferred for signal X in module Y" violations
    - ~8 "Info: unused port X in module Y" messages
    - ~5 "Warning: width mismatch on signal X expected N got M" violations
    - ~5 unique/noise lines (different patterns that don't cluster)
    - Footer section (summary counts)
  - **`tiny_report.txt`** (5 lines): Only 5 violation lines — tests the small-report fallback
  - **`sample_report.html`** (~30 lines of content): HTML table with violation data
    - Basic `<html><body><table>` structure
    - Rows with severity, message, location columns
    - ~20 violation rows with 2-3 repeating patterns
  - **`sample_report.csv`** (~25 rows): CSV with columns: severity, rule_id, message, file, line
    - ~10 rows of same violation type (different files/lines)
    - ~10 rows of another violation type
    - ~5 noise rows
  - **`empty.txt`**: Empty file (0 bytes)
  - **`sample_power_intent.txt`** (~40 lines): Power intent check report with:
    - Header with tool info
    - ~12 "Error: isolation cell missing for signal X crossing from PD_A to PD_B" violations
    - ~8 "Warning: level shifter required for signal X between VDD_0.8V and VDD_1.2V"
    - ~6 "Info: retention register X in power domain Y verified"
    - ~5 unique violations
  - All fixture files should use realistic-looking but FAKE VLSI names (e.g., `CORE_CPU`, `MEM_CTRL`, `IO_PAD`)

  **Must NOT do**:
  - Do NOT use real/proprietary VLSI data
  - Do NOT make fixtures overly complex — they test the pipeline, not real-world accuracy
  - Do NOT add more than 6-7 fixture files

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Creating text files with known content — no logic, just data
  - **Skills**: []
    - No specialized skills needed
  - **Skills Evaluated but Omitted**:
    - All skills irrelevant for fixture file creation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Tasks 2, 4, 5, 6 (all use these fixtures)
  - **Blocked By**: Task 1 (directory structure must exist)

  **References**:

  **Documentation References**:
  - Metis review identified: "Create synthetic test fixtures that mimic VLSI report patterns. Minimum 3 fixtures"
  - Draft file `.sisyphus/drafts/vlsi-report-cluster.md` — report type descriptions

  **External References**:
  - Calibre DRC report format examples (from librarian research) — mimic structure with fake data
  - SpyGlass lint report structure — use similar formatting for `sample_lint.txt`

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: All fixture files exist with expected content
    Tool: Bash
    Preconditions: Task 1 completed (directory structure exists)
    Steps:
      1. ls -la tests/fixtures/
      2. Assert: sample_lint.txt exists and size > 500 bytes
      3. Assert: tiny_report.txt exists and has exactly 5 non-empty lines
      4. Assert: sample_report.html exists and contains "<table"
      5. Assert: sample_report.csv exists and first line contains comma-separated headers
      6. Assert: empty.txt exists and size == 0
      7. Assert: sample_power_intent.txt exists and size > 300 bytes
      8. wc -l tests/fixtures/sample_lint.txt
      9. Assert: line count is between 45 and 70
    Expected Result: All fixtures present with correct structure
    Evidence: ls and wc output captured

  Scenario: Fixture content has expected patterns
    Tool: Bash
    Preconditions: Fixtures created
    Steps:
      1. grep -c "Warning:" tests/fixtures/sample_lint.txt
      2. Assert: count >= 15
      3. grep -c "Error:" tests/fixtures/sample_lint.txt
      4. Assert: count >= 8
      5. grep -c "isolation" tests/fixtures/sample_power_intent.txt
      6. Assert: count >= 10
    Expected Result: Fixtures contain repeating violation patterns suitable for clustering
    Evidence: grep counts captured
  ```

  **Commit**: YES (groups with Task 1)
  - Message: `test(fixtures): add synthetic VLSI report fixtures for testing`
  - Files: `tests/fixtures/*`
  - Pre-commit: `ls tests/fixtures/ | wc -l` (should be 6+)

---

- [x] 4. Embedder Module (Protocol + Local + OpenAI Implementations)

  **What to do**:
  - **RED**: Write tests first in `tests/test_embedder.py`:
    - `test_local_embedder_returns_numpy_array()` — given list of strings, returns numpy array of shape (n, dim)
    - `test_local_embedder_dimensions()` — output dimension is 384 (for MiniLM)
    - `test_local_embedder_similar_lines_close()` — two semantically similar lines have cosine similarity > 0.7
    - `test_local_embedder_different_lines_far()` — two unrelated lines have cosine similarity < 0.5
    - `test_embedder_protocol_compliance()` — both implementations satisfy the Protocol interface
    - `test_create_embedder_local()` — factory function returns LocalEmbedder
    - `test_create_embedder_openai()` — factory function returns OpenAIEmbedder (skip if no API key)
    - `test_embedder_empty_input()` — empty list input returns empty array
  - **GREEN**: Implement `src/vlsi_report_cluster/embedder.py`:
    - `class Embedder(Protocol)`: method `embed(lines: list[str]) -> np.ndarray`
    - `class LocalEmbedder`: uses `sentence-transformers` with configurable model name (default `all-MiniLM-L6-v2`)
    - `class OpenAIEmbedder`: uses `openai` client with configurable model (default `text-embedding-3-small`), reads `OPENAI_API_KEY` from env
    - `def create_embedder(backend: str = "local", model: str | None = None) -> Embedder` — factory function
  - **REFACTOR**: Ensure clean interface, add docstrings

  **Must NOT do**:
  - Do NOT build a plugin system or abstract factory pattern — just Protocol + 2 classes + factory function
  - Do NOT add more embedding backends (no Cohere, no HuggingFace Inference API)
  - Do NOT cache embeddings
  - Do NOT add batch processing logic beyond what sentence-transformers provides natively

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Involves external library integration (sentence-transformers, openai) with TDD
  - **Skills**: []
    - Standard Python — no specialized skills needed
  - **Skills Evaluated but Omitted**:
    - `playwright`: No browser work

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 2)
  - **Blocks**: Tasks 5, 7
  - **Blocked By**: Task 1 (project scaffold)

  **References**:

  **External References**:
  - sentence-transformers usage: https://www.sbert.net/docs/quickstart.html — `SentenceTransformer.encode()` API
  - OpenAI embeddings API: https://platform.openai.com/docs/guides/embeddings — `client.embeddings.create()` with `text-embedding-3-small`
  - Python Protocol (typing): https://docs.python.org/3/library/typing.html#typing.Protocol — duck-typing interfaces

  **WHY Each Reference Matters**:
  - sentence-transformers `encode()` returns numpy array natively — no conversion needed
  - OpenAI returns list of `Embedding` objects — need to extract `.embedding` and convert to numpy
  - Protocol ensures both implementations are interchangeable without inheritance

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_embedder.py`
  - [ ] Tests cover: local embedding, dimensions, similarity, Protocol compliance, factory, empty input
  - [ ] `pytest tests/test_embedder.py -v` → PASS (8+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Local embedder produces correct shape
    Tool: Bash
    Preconditions: Package installed with sentence-transformers
    Steps:
      1. python -c "
         from vlsi_report_cluster.embedder import create_embedder
         embedder = create_embedder('local')
         import numpy as np
         lines = ['Warning: signal CLK unconnected', 'Error: latch inferred for DATA']
         result = embedder.embed(lines)
         assert isinstance(result, np.ndarray), f'Expected ndarray, got {type(result)}'
         assert result.shape == (2, 384), f'Expected (2, 384), got {result.shape}'
         print('Shape OK')
         "
      2. Assert: stdout contains "Shape OK"
    Expected Result: Embeddings are (n, 384) numpy array
    Evidence: Command output captured

  Scenario: Similar lines have high cosine similarity
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. python -c "
         from vlsi_report_cluster.embedder import create_embedder
         import numpy as np
         embedder = create_embedder('local')
         lines = [
           'Warning: signal CLK is unconnected at module CPU',
           'Warning: signal RST is unconnected at module GPU',
           'Error: latch inferred for signal DATA in module MEM'
         ]
         vecs = embedder.embed(lines)
         # Cosine similarity between line 0 and 1 (similar)
         sim_01 = np.dot(vecs[0], vecs[1]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1]))
         # Cosine similarity between line 0 and 2 (different)
         sim_02 = np.dot(vecs[0], vecs[2]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[2]))
         print(f'Similar: {sim_01:.3f}, Different: {sim_02:.3f}')
         assert sim_01 > sim_02, 'Similar lines should have higher similarity'
         print('Similarity ordering OK')
         "
      2. Assert: stdout contains "Similarity ordering OK"
    Expected Result: Semantically similar lines cluster closer in embedding space
    Evidence: Similarity scores captured
  ```

  **Commit**: YES
  - Message: `feat(embedder): add pluggable embedding engine with local and OpenAI backends`
  - Files: `src/vlsi_report_cluster/embedder.py`, `tests/test_embedder.py`
  - Pre-commit: `pytest tests/test_embedder.py -v`

---

- [x] 5. Clusterer Module (HDBSCAN + Small-Report Fallback)

  **What to do**:
  - **RED**: Write tests first in `tests/test_clusterer.py`:
    - `test_cluster_distinct_groups()` — given embeddings of 3 clearly different violation types (15 each), returns 3 clusters
    - `test_cluster_labels_shape()` — output labels array has same length as input
    - `test_cluster_noise_points()` — some lines labeled as -1 (noise)
    - `test_cluster_small_report_fallback()` — given fewer embeddings than `min_cluster_size * 2`, returns `None` (signaling fallback needed)
    - `test_cluster_high_noise_fallback()` — if >80% of points are noise, returns `None`
    - `test_cluster_min_cluster_size_parameter()` — `min_cluster_size` parameter affects results
    - `test_cluster_returns_metadata()` — result includes number of clusters found, noise count
  - **GREEN**: Implement `src/vlsi_report_cluster/clusterer.py`:
    - `@dataclass ClusterResult`: `labels: np.ndarray`, `n_clusters: int`, `n_noise: int`, `is_fallback: bool`
    - `def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 3, min_samples: int = 2) -> ClusterResult | None`:
      - If `len(embeddings) < min_cluster_size * 2`: return `None` (too small for HDBSCAN)
      - Run HDBSCAN with `cluster_selection_method='leaf'`
      - If >80% of points labeled as noise: return `None` (fallback signal)
      - Otherwise return `ClusterResult` with labels and metadata
  - **REFACTOR**: Ensure clean API, docstrings

  **Must NOT do**:
  - Do NOT implement the Drain3-only fallback IN this module — that logic goes in the pipeline/CLI integration (Task 7)
  - Do NOT add K-Means or DBSCAN alternatives
  - Do NOT add dimensionality reduction (UMAP/PCA) before clustering
  - Do NOT tune hyperparameters automatically

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: HDBSCAN edge cases (small reports, high noise) require careful logic and understanding of density-based clustering behavior
  - **Skills**: []
    - No specialized skills needed — pure algorithmic Python
  - **Skills Evaluated but Omitted**:
    - All skills irrelevant for clustering algorithm work

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (with Task 6 partial overlap possible)
  - **Blocks**: Tasks 6, 7
  - **Blocked By**: Tasks 2, 4 (needs parser + embedder working to validate end-to-end)

  **References**:

  **External References**:
  - HDBSCAN docs: https://hdbscan.readthedocs.io/en/latest/api.html — `HDBSCAN` class parameters
  - HDBSCAN `cluster_selection_method='leaf'`: gives finer-grained clusters — better for VLSI reports with many subtypes
  - Metis review: "If report has <10 lines or HDBSCAN marks >80% as noise, skip and use Drain3-only fallback"

  **WHY Each Reference Matters**:
  - `min_cluster_size=3` and `min_samples=2` are intentionally low for VLSI reports where even 3 similar violations form a meaningful group
  - `cluster_selection_method='leaf'` avoids merging distinct violation subtypes into one large cluster
  - Fallback threshold (80% noise) comes from Metis analysis — below this, HDBSCAN isn't finding structure

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_clusterer.py`
  - [ ] Tests cover: distinct groups, label shape, noise points, small report fallback, high-noise fallback, parameter effect, metadata
  - [ ] `pytest tests/test_clusterer.py -v` → PASS (7+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: HDBSCAN clusters distinct violation types
    Tool: Bash
    Preconditions: Package installed, embedder working
    Steps:
      1. python -c "
         from vlsi_report_cluster.embedder import create_embedder
         from vlsi_report_cluster.clusterer import cluster_embeddings
         embedder = create_embedder('local')
         lines = (
           ['Warning: signal CLK unconnected at module CPU_' + str(i) for i in range(15)] +
           ['Error: latch inferred for signal DATA in module MEM_' + str(i) for i in range(15)] +
           ['Info: unused port SCAN_EN in module IO_' + str(i) for i in range(10)]
         )
         vecs = embedder.embed(lines)
         result = cluster_embeddings(vecs, min_cluster_size=3)
         assert result is not None, 'Should find clusters'
         print(f'Clusters: {result.n_clusters}, Noise: {result.n_noise}')
         assert result.n_clusters >= 2, f'Expected >=2 clusters, got {result.n_clusters}'
         print('Clustering OK')
         "
      2. Assert: stdout contains "Clustering OK"
    Expected Result: At least 2-3 distinct clusters found
    Evidence: Cluster counts captured

  Scenario: Small report triggers fallback
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. python -c "
         from vlsi_report_cluster.clusterer import cluster_embeddings
         import numpy as np
         # 5 random vectors — too small for HDBSCAN
         vecs = np.random.rand(5, 384)
         result = cluster_embeddings(vecs, min_cluster_size=3)
         assert result is None, 'Should return None for small input'
         print('Small report fallback OK')
         "
      2. Assert: stdout contains "Small report fallback OK"
    Expected Result: Returns None to signal fallback needed
    Evidence: Command output captured
  ```

  **Commit**: YES
  - Message: `feat(clusterer): add HDBSCAN clustering with small-report fallback detection`
  - Files: `src/vlsi_report_cluster/clusterer.py`, `tests/test_clusterer.py`
  - Pre-commit: `pytest tests/test_clusterer.py -v`

---

- [ ] 6. Template Extractor Module (Drain3 Per Cluster)

  **What to do**:
  - **RED**: Write tests first in `tests/test_template_extractor.py`:
    - `test_extract_template_from_similar_lines()` — given 5 similar lines, returns a template with `<*>` wildcards
    - `test_extract_values_from_template()` — returns the actual values that replaced wildcards
    - `test_fresh_drain_per_cluster()` — two different clusters produce independent templates (no state leak)
    - `test_extract_from_all_clusters()` — given lines + labels, returns list of `ClusterTemplate` results
    - `test_extract_single_line_cluster()` — cluster with 1 line returns the line itself as template (no wildcards)
    - `test_extract_noise_lines()` — noise lines (label=-1) returned separately
    - `test_drain3_only_mode()` — fallback mode: no labels, Drain3 processes all lines directly
  - **GREEN**: Implement `src/vlsi_report_cluster/template_extractor.py`:
    - `@dataclass ClusterTemplate`: `cluster_id: int`, `template: str`, `count: int`, `values: list[list[str]]` (list of extracted value tuples per line)
    - `@dataclass ExtractionResult`: `clusters: list[ClusterTemplate]`, `noise_lines: list[str]`, `is_fallback: bool`
    - `def extract_templates(lines: list[str], labels: np.ndarray | None = None) -> ExtractionResult`:
      - If `labels is None`: Drain3-only fallback mode — process all lines with single TemplateMiner
      - If `labels` provided: group lines by cluster label, create **fresh `TemplateMiner()` per cluster**, extract template + values
      - Collect noise lines (label=-1) separately
    - Use `drain3.TemplateMiner` with default config (sim_th=0.4, depth=4)
    - Use `template_miner.extract_parameters(template, log_line)` to get values

  **Must NOT do**:
  - Do NOT reuse TemplateMiner across clusters (CRITICAL — Metis guardrail)
  - Do NOT add custom Drain3 masking instructions
  - Do NOT modify Drain3 config beyond defaults
  - Do NOT persist Drain3 state

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: Drain3 API is nuanced — state management, template extraction, parameter extraction all need careful handling
  - **Skills**: []
    - Standard Python with external library integration
  - **Skills Evaluated but Omitted**:
    - All skills irrelevant for template extraction logic

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 5 clusterer output format)
  - **Parallel Group**: Wave 3 (after Task 5)
  - **Blocks**: Task 7
  - **Blocked By**: Task 5 (needs ClusterResult format defined)

  **References**:

  **External References**:
  - Drain3 API: https://github.com/logpai/Drain3 — `TemplateMiner.add_log_message()` returns `{"change_type", "cluster_id", "cluster_size", "template_mined"}`
  - Drain3 `extract_parameters()`: `template_miner.drain.extract_parameters(template_str, log_line)` → extracts values that were replaced by `<*>`
  - Drain3 config: `sim_th=0.4` (similarity threshold), `depth=4` (parse tree depth), `max_children=100`

  **WHY Each Reference Matters**:
  - `add_log_message()` is called sequentially for each line in a cluster — templates emerge incrementally
  - `extract_parameters()` is the key API for the "values" part of the output (Template + count + **values**)
  - Fresh `TemplateMiner()` per cluster prevents state leakage — Drain3's internal prefix tree would merge templates across clusters otherwise

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_template_extractor.py`
  - [ ] Tests cover: template extraction, value extraction, fresh drain per cluster, all clusters, single-line, noise, fallback mode
  - [ ] `pytest tests/test_template_extractor.py -v` → PASS (7+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Template extraction produces wildcards
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. python -c "
         from vlsi_report_cluster.template_extractor import extract_templates
         import numpy as np
         lines = [
           'Warning: signal CLK unconnected at module CPU_0',
           'Warning: signal RST unconnected at module CPU_1',
           'Warning: signal DATA unconnected at module GPU_0',
           'Error: latch inferred for signal ADDR in module MEM_0',
           'Error: latch inferred for signal CTRL in module MEM_1',
         ]
         labels = np.array([0, 0, 0, 1, 1])
         result = extract_templates(lines, labels)
         print(f'Clusters: {len(result.clusters)}')
         for c in result.clusters:
             print(f'  Cluster {c.cluster_id}: template=\"{c.template}\", count={c.count}')
             print(f'    Values: {c.values}')
         assert len(result.clusters) == 2, 'Expected 2 clusters'
         assert '<*>' in result.clusters[0].template, 'Template should have wildcards'
         print('Template extraction OK')
         "
      2. Assert: stdout contains "Template extraction OK"
      3. Assert: stdout contains "<*>"
    Expected Result: Templates with wildcards, values extracted
    Evidence: Template strings and values captured

  Scenario: Drain3-only fallback mode works
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. python -c "
         from vlsi_report_cluster.template_extractor import extract_templates
         lines = [
           'Warning: signal CLK unconnected at module CPU',
           'Warning: signal RST unconnected at module GPU',
           'Error: latch inferred for DATA',
         ]
         result = extract_templates(lines, labels=None)  # No labels = fallback
         assert result.is_fallback == True
         assert len(result.clusters) >= 1
         print(f'Fallback clusters: {len(result.clusters)}')
         print('Fallback mode OK')
         "
      2. Assert: stdout contains "Fallback mode OK"
    Expected Result: Drain3 processes all lines without HDBSCAN labels
    Evidence: Command output captured
  ```

  **Commit**: YES
  - Message: `feat(template): add Drain3-based template extraction with per-cluster isolation`
  - Files: `src/vlsi_report_cluster/template_extractor.py`, `tests/test_template_extractor.py`
  - Pre-commit: `pytest tests/test_template_extractor.py -v`

---

- [ ] 7. CLI Integration (Typer + Rich Output + JSON + Full Pipeline)

  **What to do**:
  - **RED**: Write tests first in `tests/test_cli.py`:
    - `test_cli_text_report_output()` — run CLI on sample_lint.txt, assert exit code 0, stdout has cluster info
    - `test_cli_json_output()` — `--output-format json` produces valid JSON with expected keys
    - `test_cli_small_report_fallback()` — tiny_report.txt triggers fallback, still produces output
    - `test_cli_html_report()` — sample_report.html auto-detected and processed
    - `test_cli_csv_report()` — sample_report.csv auto-detected and processed
    - `test_cli_empty_file_error()` — empty.txt produces error message, non-zero exit
    - `test_cli_nonexistent_file()` — missing file produces error, exit code 2
    - `test_cli_format_override()` — `--format text` works
    - `test_cli_min_cluster_size()` — `--min-cluster-size 5` parameter works
    - `test_cli_encoding_flag()` — `--encoding utf-8` accepted
    - `test_cli_embedder_flag()` — `--embedder local` accepted
  - **GREEN**: Implement `src/vlsi_report_cluster/cli.py` and `src/vlsi_report_cluster/formatter.py`:
    - **cli.py**: Typer app with main command:
      ```python
      @app.command()
      def cluster(
          report_file: Path,
          output_format: str = "table",  # "table" or "json"
          format: str | None = None,  # override format detection
          min_cluster_size: int = 3,
          min_samples: int = 2,
          embedder: str = "local",
          embedder_model: str | None = None,
          encoding: str = "utf-8",
      )
      ```
    - Pipeline orchestration:
      1. `parse_report(report_file, format, encoding)` → lines
      2. If no lines: print error, exit 1
      3. `create_embedder(embedder, embedder_model)` → embedder
      4. `embedder.embed(lines)` → vectors
      5. `cluster_embeddings(vectors, min_cluster_size, min_samples)` → result or None
      6. If None (fallback): `extract_templates(lines, labels=None)` → Drain3-only
      7. Else: `extract_templates(lines, result.labels)` → clustered templates
      8. Format output (table or JSON) and print
    - **formatter.py**:
      - `def format_table(result: ExtractionResult) -> str` — Rich table with columns: Cluster, Template, Count, Sample Values
      - `def format_json(result: ExtractionResult) -> str` — JSON with `{"clusters": [...], "unclustered": [...], "metadata": {...}}`
    - **`__main__.py`**: `from vlsi_report_cluster.cli import app; app()`

  **Must NOT do**:
  - Do NOT add interactive mode
  - Do NOT add progress bars (embedding is fast enough on CPU for single files)
  - Do NOT add `--verbose` or logging framework
  - Do NOT add export to file (just stdout)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integration task connecting all modules — needs to handle all edge cases and produce polished output
  - **Skills**: []
    - Standard Python CLI work — Typer/Rich are well-documented
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI, just CLI
    - `playwright`: No browser work

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (sequential — depends on all modules)
  - **Blocks**: Task 8
  - **Blocked By**: Tasks 2, 4, 5, 6 (all pipeline modules)

  **References**:

  **Pattern References**:
  - `src/vlsi_report_cluster/parser.py` — `parse_report()` function signature and return type
  - `src/vlsi_report_cluster/embedder.py` — `create_embedder()` factory and `Embedder.embed()` Protocol
  - `src/vlsi_report_cluster/clusterer.py` — `cluster_embeddings()` return type `ClusterResult | None`
  - `src/vlsi_report_cluster/template_extractor.py` — `extract_templates()` return type `ExtractionResult`

  **External References**:
  - Typer docs: https://typer.tiangolo.com/ — command definition, parameters, exit codes
  - Rich tables: https://rich.readthedocs.io/en/stable/tables.html — `Table` class for terminal output
  - Rich console: https://rich.readthedocs.io/en/stable/console.html — `Console` for stderr error messages

  **WHY Each Reference Matters**:
  - Typer handles CLI argument parsing, type validation, and help text generation automatically
  - Rich Table provides aligned columns with colors — better than print() for cluster output
  - All module references are needed because cli.py calls every module in sequence

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_cli.py`
  - [ ] Tests cover: text report, JSON, small report, HTML, CSV, empty file, nonexistent file, parameters
  - [ ] `pytest tests/test_cli.py -v` → PASS (11+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Full pipeline on lint report (table output)
    Tool: Bash
    Preconditions: Package installed, all modules implemented, fixtures exist
    Steps:
      1. vlsi-report-cluster tests/fixtures/sample_lint.txt
      2. Assert: exit code 0
      3. Assert: stdout contains "Cluster" (table header)
      4. Assert: stdout contains "<*>" (template wildcards)
      5. Assert: stdout contains at least 2 cluster entries
    Expected Result: Clustered violations displayed as rich table
    Evidence: Full stdout captured to .sisyphus/evidence/task-7-table-output.txt

  Scenario: JSON output is valid and complete
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. vlsi-report-cluster tests/fixtures/sample_lint.txt --output-format json > /tmp/vlsi_output.json
      2. Assert: exit code 0
      3. python -c "
         import json
         with open('/tmp/vlsi_output.json') as f:
             data = json.load(f)
         assert 'clusters' in data, 'Missing clusters key'
         assert isinstance(data['clusters'], list), 'clusters must be list'
         for c in data['clusters']:
             assert 'template' in c, 'Missing template'
             assert 'count' in c, 'Missing count'
             assert 'values' in c, 'Missing values'
         print(f'Valid JSON with {len(data[\"clusters\"])} clusters')
         print('JSON validation OK')
         "
      4. Assert: stdout contains "JSON validation OK"
    Expected Result: Valid JSON with clusters array, each having template/count/values
    Evidence: JSON file saved at /tmp/vlsi_output.json

  Scenario: Small report uses Drain3-only fallback
    Tool: Bash
    Preconditions: Package installed, tiny_report.txt exists
    Steps:
      1. vlsi-report-cluster tests/fixtures/tiny_report.txt --output-format json 2>&1
      2. Assert: exit code 0
      3. Assert: output is valid JSON or contains "fallback" indicator
    Expected Result: Tool handles small reports without crashing
    Evidence: Output captured

  Scenario: Empty file produces clear error
    Tool: Bash
    Preconditions: Package installed, empty.txt exists
    Steps:
      1. vlsi-report-cluster tests/fixtures/empty.txt 2>&1
      2. Assert: exit code is non-zero (1 or 2)
      3. Assert: stderr or stdout contains error message (not a Python traceback)
    Expected Result: User-friendly error message, not stack trace
    Evidence: Error output captured

  Scenario: Nonexistent file produces clear error
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. vlsi-report-cluster nonexistent_file.txt 2>&1
      2. Assert: exit code is non-zero
      3. Assert: output contains "not found" or "does not exist" (case insensitive)
    Expected Result: File-not-found error with helpful message
    Evidence: Error output captured
  ```

  **Commit**: YES
  - Message: `feat(cli): integrate full pipeline with Typer CLI, Rich table output, and JSON export`
  - Files: `src/vlsi_report_cluster/cli.py`, `src/vlsi_report_cluster/formatter.py`, `src/vlsi_report_cluster/__main__.py`, `tests/test_cli.py`
  - Pre-commit: `pytest tests/ -v`

---

- [ ] 8. Edge Cases, Error Handling, and README

  **What to do**:
  - **Edge case hardening**:
    - Add try/except around embedding model loading (catch `OSError` if model not downloaded yet, print helpful message)
    - Handle `UnicodeDecodeError` for files with wrong encoding — print message suggesting `--encoding` flag
    - Handle reports where ALL lines are filtered out (only headers/separators) — clear error
    - Handle reports where all lines are identical — Drain3 produces single template, count=N
    - Test with `sample_power_intent.txt` fixture to verify multi-pattern reports work
  - **Error messages**: All errors should be user-friendly (no Python tracebacks), using `rich.console.Console(stderr=True)` for error output
  - **Write tests** in `tests/test_edge_cases.py`:
    - `test_all_identical_lines()` — 20 identical lines produce 1 cluster with count=20
    - `test_all_unique_lines()` — 20 completely different lines → mostly noise, fallback to Drain3
    - `test_unicode_file()` — file with unicode characters (non-ASCII module names) parses correctly
    - `test_very_long_lines()` — lines >1000 chars don't crash
    - `test_mixed_severity_patterns()` — report with Warning/Error/Info patterns clusters by content, not severity keyword
  - **README.md**: Create with:
    - Project description (1 paragraph)
    - Installation: `pip install -e .` and `pip install -e ".[openai]"`
    - Usage examples (3-4 commands)
    - Output format description
    - CLI options reference table
    - Note about first-run model download (~90MB for MiniLM)
    - Architecture diagram (text-based pipeline)

  **Must NOT do**:
  - Do NOT add logging framework (keep it simple — stderr for errors, stdout for results)
  - Do NOT add retry logic
  - Do NOT add telemetry or analytics

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Edge case handling and documentation require attention to detail
  - **Skills**: []
    - Standard Python + documentation writing
  - **Skills Evaluated but Omitted**:
    - All skills irrelevant

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Task 7)
  - **Blocks**: None (final task)
  - **Blocked By**: Task 7 (needs full pipeline working)

  **References**:

  **Pattern References**:
  - `src/vlsi_report_cluster/cli.py` — error handling wraps around the pipeline here
  - `tests/fixtures/sample_power_intent.txt` — multi-pattern fixture for integration testing
  - All existing test files — follow same patterns for `test_edge_cases.py`

  **External References**:
  - Rich Console stderr: https://rich.readthedocs.io/en/stable/console.html#error-console — `Console(stderr=True)` for error output
  - sentence-transformers model download behavior: first call to `SentenceTransformer('all-MiniLM-L6-v2')` downloads ~90MB — should be documented

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/test_edge_cases.py`
  - [ ] Tests cover: all identical, all unique, unicode, long lines, mixed severity
  - [ ] `pytest tests/test_edge_cases.py -v` → PASS (5+ tests, 0 failures)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Full test suite passes
    Tool: Bash
    Preconditions: All modules implemented
    Steps:
      1. pytest tests/ -v --tb=short 2>&1
      2. Assert: exit code 0
      3. Assert: stdout contains "passed"
      4. Assert: stdout does NOT contain "FAILED"
      5. Count total tests — should be 40+
    Expected Result: All tests pass
    Evidence: Full pytest output captured to .sisyphus/evidence/task-8-full-tests.txt

  Scenario: End-to-end with power intent report
    Tool: Bash
    Preconditions: All modules implemented
    Steps:
      1. vlsi-report-cluster tests/fixtures/sample_power_intent.txt
      2. Assert: exit code 0
      3. Assert: stdout contains "isolation" or "<*>" (template wildcards)
      4. Assert: stdout shows multiple clusters
    Expected Result: Power intent report clusters correctly
    Evidence: Output captured

  Scenario: README is readable and accurate
    Tool: Bash
    Preconditions: README.md created
    Steps:
      1. cat README.md | head -50
      2. Assert: Contains "# " (has title)
      3. Assert: Contains "pip install" (has installation)
      4. Assert: Contains "vlsi-report-cluster" (has usage)
      5. Assert: Contains "--output-format" (documents options)
    Expected Result: README has all required sections
    Evidence: Head of README captured

  Scenario: Encoding error is handled gracefully
    Tool: Bash
    Preconditions: Create a Latin-1 encoded file
    Steps:
      1. python -c "
         with open('/tmp/latin1_report.txt', 'w', encoding='latin-1') as f:
             f.write('Warning: signal \xe9 unconnected\n' * 5)
         "
      2. vlsi-report-cluster /tmp/latin1_report.txt 2>&1
      3. Assert: No Python traceback in output
      4. Assert: Either succeeds or shows user-friendly error suggesting --encoding
    Expected Result: Graceful error handling, not stack trace
    Evidence: Error output captured
  ```

  **Commit**: YES
  - Message: `feat(hardening): add edge case handling, error messages, and README documentation`
  - Files: `tests/test_edge_cases.py`, `README.md`, updated `src/vlsi_report_cluster/cli.py`
  - Pre-commit: `pytest tests/ -v`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(init): scaffold project with pyproject.toml, src layout, and test infrastructure` | pyproject.toml, src/**/*.py, tests/conftest.py | pip install + pytest |
| 3 | `test(fixtures): add synthetic VLSI report fixtures for testing` | tests/fixtures/* | ls + grep |
| 2 | `feat(parser): add report parser with format detection and line extraction` | parser.py, test_parser.py | pytest tests/test_parser.py |
| 4 | `feat(embedder): add pluggable embedding engine with local and OpenAI backends` | embedder.py, test_embedder.py | pytest tests/test_embedder.py |
| 5 | `feat(clusterer): add HDBSCAN clustering with small-report fallback detection` | clusterer.py, test_clusterer.py | pytest tests/test_clusterer.py |
| 6 | `feat(template): add Drain3-based template extraction with per-cluster isolation` | template_extractor.py, test_template_extractor.py | pytest tests/test_template_extractor.py |
| 7 | `feat(cli): integrate full pipeline with Typer CLI, Rich table output, and JSON export` | cli.py, formatter.py, __main__.py, test_cli.py | pytest tests/ |
| 8 | `feat(hardening): add edge case handling, error messages, and README documentation` | test_edge_cases.py, README.md, cli.py updates | pytest tests/ |

---

## Success Criteria

### Verification Commands
```bash
# Install
pip install -e ".[dev]" # Expected: Successfully installed

# Run on text report
vlsi-report-cluster tests/fixtures/sample_lint.txt
# Expected: Rich table with 3-4 clusters, templates with <*>, counts, values

# Run with JSON output
vlsi-report-cluster tests/fixtures/sample_lint.txt --output-format json | python -m json.tool
# Expected: Valid JSON with clusters array

# Run on HTML report
vlsi-report-cluster tests/fixtures/sample_report.html
# Expected: Clusters extracted from HTML content

# Run on tiny report (fallback)
vlsi-report-cluster tests/fixtures/tiny_report.txt
# Expected: Output (possibly with fallback notice), no crash

# Run on empty file
vlsi-report-cluster tests/fixtures/empty.txt
# Expected: Error message, non-zero exit code

# Full test suite
pytest tests/ -v --cov=vlsi_report_cluster
# Expected: 40+ tests, all passing
```

### Final Checklist
- [ ] `pip install -e .` works
- [ ] CLI processes text, HTML, and CSV reports
- [ ] HDBSCAN finds meaningful clusters in medium+ reports
- [ ] Small reports fallback to Drain3-only mode gracefully
- [ ] Templates contain `<*>` wildcards for variable parts
- [ ] Extracted values are shown per cluster
- [ ] JSON output is valid and machine-parseable
- [ ] Empty/missing files produce user-friendly errors
- [ ] No report-type-specific logic exists
- [ ] No persistent state between runs
- [ ] All tests pass
- [ ] README documents installation, usage, and CLI options
