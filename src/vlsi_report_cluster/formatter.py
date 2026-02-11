"""Formatter module for output formatting.

This module provides formatters for CLI output:
- format_table: Rich table output with clusters and templates
- format_json: JSON output for programmatic use
"""

import io
import json

from rich.console import Console
from rich.table import Table

from vlsi_report_cluster.template_extractor import ExtractionResult


def format_table(result: ExtractionResult) -> str:
    """Format extraction result as a Rich table.
    
    Creates a table with columns:
    - Cluster: Cluster ID or "Unclustered"
    - Template: The extracted template pattern
    - Count: Number of lines matching the template
    - Sample Values: First 2-3 examples of extracted parameter values
    
    Args:
        result: ExtractionResult from extract_templates()
        
    Returns:
        Formatted table as a string
    """
    # Create table with Rich
    table = Table(title="VLSI Report Clustering Results", show_header=True, header_style="bold magenta")
    table.add_column("Cluster", style="cyan", justify="right")
    table.add_column("Template", style="green")
    table.add_column("Count", style="yellow", justify="right")
    table.add_column("Sample Values", style="white")
    
    # Add cluster rows
    for cluster in result.clusters:
        # Format sample values (first 2-3 examples)
        sample_count = min(3, len(cluster.values))
        samples = []
        for i in range(sample_count):
            value_list = cluster.values[i]
            if value_list:
                # Join multiple values with " | "
                samples.append(" | ".join(value_list))
            else:
                samples.append("(no params)")
        
        sample_str = "\n".join(samples) if samples else "(no samples)"
        
        table.add_row(
            str(cluster.cluster_id),
            cluster.template,
            str(cluster.count),
            sample_str,
        )
    
    # Add unclustered section if there are noise lines
    if result.noise_lines:
        table.add_section()
        # Show first 5 unclustered lines
        noise_count = min(5, len(result.noise_lines))
        noise_samples = "\n".join(result.noise_lines[:noise_count])
        if len(result.noise_lines) > noise_count:
            noise_samples += f"\n... and {len(result.noise_lines) - noise_count} more"
        
        table.add_row(
            "Unclustered",
            "(no template)",
            str(len(result.noise_lines)),
            noise_samples,
        )
    
    # Capture table output to string
    console = Console(file=io.StringIO(), force_terminal=True, width=120)
    console.print(table)
    output = console.file.getvalue()  # type: ignore
    
    return output


def format_json(result: ExtractionResult) -> str:
    """Format extraction result as JSON.
    
    Creates a JSON object with:
    - clusters: List of cluster objects with cluster_id, template, count, values
    - unclustered: List of noise lines
    - metadata: Dict with is_fallback, total_clusters, total_noise, etc.
    
    Args:
        result: ExtractionResult from extract_templates()
        
    Returns:
        JSON string (pretty-printed with indent=2)
    """
    # Build clusters list
    clusters_data = []
    for cluster in result.clusters:
        clusters_data.append({
            "cluster_id": cluster.cluster_id,
            "template": cluster.template,
            "count": cluster.count,
            "values": cluster.values,
        })
    
    # Build metadata
    metadata = {
        "is_fallback": result.is_fallback,
        "total_clusters": len(result.clusters),
        "total_noise": len(result.noise_lines),
        "clustering_mode": "drain3_only" if result.is_fallback else "hdbscan_drain3",
    }
    
    # Build final JSON structure
    data = {
        "clusters": clusters_data,
        "unclustered": result.noise_lines,
        "metadata": metadata,
    }
    
    return json.dumps(data, indent=2)
