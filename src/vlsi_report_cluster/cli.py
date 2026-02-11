"""Command-line interface for vlsi-report-cluster."""


class _MockApp:
    """Mock app when typer is not available."""
    
    def __call__(self):
        """Allow app to be called."""
        pass


try:
    import typer
    
    app = typer.Typer(
        name="vlsi-report-cluster",
        help="VLSI Report Clustering and Analysis Tool",
    )

    @app.command()
    def main(
        input_file: str = typer.Argument(..., help="Input report file"),
    ) -> None:
        """Process and cluster VLSI reports."""
        pass
except ImportError:
    # Fallback for when typer is not installed
    app = _MockApp()


def main() -> None:
    """Main entry point for CLI."""
    if hasattr(app, "__call__"):
        app()

