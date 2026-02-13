"""Command-line interface for vlsi-report-cluster."""

# pyright: reportMissingImports=false

from pathlib import Path
import sys

try:
    import typer
except ModuleNotFoundError as e:
    print(f"Error: Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install vlsi-report-cluster", file=sys.stderr)
    raise SystemExit(1) from e

try:
    from rich.console import Console
except ModuleNotFoundError as e:
    print(f"Error: Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install vlsi-report-cluster", file=sys.stderr)
    raise SystemExit(1) from e

from vlsi_report_cluster.clusterer import cluster_embeddings
from vlsi_report_cluster.config import get_openai_base_url, load_config
from vlsi_report_cluster.embedder import create_embedder
from vlsi_report_cluster.formatter import format_json, format_table
from vlsi_report_cluster.parser import parse_report
from vlsi_report_cluster.template_extractor import extract_templates


app = typer.Typer(
    name="vlsi-report-cluster",
    help="VLSI Report Clustering and Analysis Tool",
)


@app.command()
def main(
    report_file: Path = typer.Argument(..., help="Input report file", exists=True),
    output_format: str = typer.Option("table", help="Output format: table or json"),
    format: str | None = typer.Option(None, help="Override format detection (text, html, csv)"),
    config_file: Path | None = typer.Option(
        None,
        "--config",
        help="Path to JSON config file",
    ),
    min_cluster_size: int = typer.Option(3, help="HDBSCAN min cluster size"),
    min_samples: int = typer.Option(2, help="HDBSCAN min samples"),
    embedder: str = typer.Option("local", help="Embedding backend: local or openai"),
    embedder_model: str | None = typer.Option(None, help="Custom embedding model"),
    encoding: str = typer.Option("utf-8", help="File encoding"),
) -> None:
    """Process and cluster VLSI reports.

    Full pipeline: parse → embed → cluster → extract → format

    Supports text, HTML, and CSV report formats.
    Output can be formatted as a Rich table (default) or JSON.
    """
    console = Console(stderr=True)

    try:
        config = load_config(config_file)
        openai_base_url = None
        if embedder == "openai":
            openai_base_url = get_openai_base_url(config)

        lines = parse_report(report_file, format=format, encoding=encoding)
        if not lines:
            console.print("[red]Error: No lines found in report[/red]")
            raise typer.Exit(1)

        embedder_instance = create_embedder(
            embedder,
            embedder_model,
            openai_base_url=openai_base_url,
        )
        vectors = embedder_instance.embed(lines)
        cluster_result = cluster_embeddings(vectors, min_cluster_size, min_samples)

        if cluster_result is None:
            extraction = extract_templates(lines, labels=None)
        else:
            extraction = extract_templates(lines, cluster_result.labels)

        if output_format == "json":
            output = format_json(extraction)
        elif output_format == "table":
            output = format_table(extraction)
        else:
            console.print(
                f"[red]Error: Unsupported --output-format '{output_format}'. Use 'table' or 'json'.[/red]"
            )
            raise typer.Exit(2)

        print(output)

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {report_file}[/red]")
        raise typer.Exit(2)
    except UnicodeDecodeError:
        console.print("[red]Error: Unable to decode file. Try --encoding parameter[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except OSError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print(
            "[yellow]Hint: Check internet connection for first-time model download[/yellow]"
        )
        raise typer.Exit(1)
    except ModuleNotFoundError as e:
        console.print(f"[red]Error: Missing dependency: {e}[/red]")
        console.print("[yellow]Install with: pip install vlsi-report-cluster[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def cli_main() -> None:
    """Main entry point for CLI."""
    app()
