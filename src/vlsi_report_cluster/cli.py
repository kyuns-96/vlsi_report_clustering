"""Command-line interface for vlsi-report-cluster."""

from pathlib import Path

try:
    import typer
    from rich.console import Console
    
    from vlsi_report_cluster.parser import parse_report
    from vlsi_report_cluster.embedder import create_embedder
    from vlsi_report_cluster.clusterer import cluster_embeddings
    from vlsi_report_cluster.template_extractor import extract_templates
    from vlsi_report_cluster.formatter import format_table, format_json
    
    app = typer.Typer(
        name="vlsi-report-cluster",
        help="VLSI Report Clustering and Analysis Tool",
    )

    @app.command()
    def main(
        report_file: Path = typer.Argument(..., help="Input report file", exists=True),
        output_format: str = typer.Option("table", help="Output format: table or json"),
        format: str | None = typer.Option(None, help="Override format detection (text, html, csv)"),
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
            # Step 1: Parse report
            lines = parse_report(report_file, format, encoding)
            
            if not lines:
                console.print("[red]Error: No lines found in report[/red]")
                raise typer.Exit(1)
            
            # Step 2: Create embedder
            embedder_instance = create_embedder(embedder, embedder_model)
            
            # Step 3: Embed lines
            vectors = embedder_instance.embed(lines)
            
            # Step 4: Cluster embeddings
            cluster_result = cluster_embeddings(vectors, min_cluster_size, min_samples)
            
            # Step 5: Extract templates with fallback handling
            if cluster_result is None:
                # Small report or high noise - use Drain3-only fallback
                extraction = extract_templates(lines, labels=None)
            else:
                # Normal clustering path
                extraction = extract_templates(lines, cluster_result.labels)
            
            # Step 6: Format output
            if output_format == "json":
                output = format_json(extraction)
            else:
                output = format_table(extraction)
            
            # Step 7: Print to stdout
            print(output)
            
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {report_file}[/red]")
            raise typer.Exit(2)
        except UnicodeDecodeError:
            console.print(f"[red]Error: Unable to decode file. Try --encoding parameter[/red]")
            raise typer.Exit(1)
        except ImportError as e:
            console.print(f"[red]Error: Missing dependency: {e}[/red]")
            console.print("[yellow]Install with: pip install vlsi-report-cluster[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

except ImportError:
    # Fallback for when typer is not installed
    class _MockApp:
        """Mock app when typer is not available."""
        
        def __call__(self):
            """Allow app to be called."""
            pass
    
    app = _MockApp()


def cli_main() -> None:
    """Main entry point for CLI."""
    app()

