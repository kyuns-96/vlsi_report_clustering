#!/usr/bin/env python3
"""
Embedder Module API Demonstration
==================================

This script demonstrates the complete API of the embedder module.
Run with: python3 EMBEDDER_API_DEMO.py

Requirements:
  - sentence-transformers>=2.2.0
  - openai>=1.0.0 (optional, for OpenAI embedder)
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from vlsi_report_cluster.embedder import create_embedder, LocalEmbedder, OpenAIEmbedder, Embedder


def demo_local_embedder():
    """Demonstrate LocalEmbedder usage."""
    print("=" * 70)
    print("DEMO 1: LocalEmbedder with sentence-transformers")
    print("=" * 70)
    
    # Create embedder (downloads model on first use)
    embedder = LocalEmbedder()
    
    # Example VLSI violation messages
    lines = [
        "Warning: signal CLK is unconnected at module CPU",
        "Warning: signal RST is unconnected at module GPU",
        "Error: latch inferred for signal DATA in module MEM",
    ]
    
    # Generate embeddings
    embeddings = embedder.embed(lines)
    print(f"\nInput: {len(lines)} lines")
    print(f"Output shape: {embeddings.shape}")
    print(f"Expected: ({len(lines)}, 384)")
    
    # Compute semantic similarity
    vec0 = embeddings[0] / np.linalg.norm(embeddings[0])
    vec1 = embeddings[1] / np.linalg.norm(embeddings[1])
    vec2 = embeddings[2] / np.linalg.norm(embeddings[2])
    
    sim_01 = np.dot(vec0, vec1)  # Similar warnings
    sim_02 = np.dot(vec0, vec2)  # Warning vs Error
    
    print(f"\nSemantic Similarity:")
    print(f"  Warning CLK vs Warning RST: {sim_01:.3f} (similar)")
    print(f"  Warning CLK vs Error latch: {sim_02:.3f} (different)")
    print(f"  Expected: similar > 0.7, different < 0.5")
    print()


def demo_factory_function():
    """Demonstrate factory function usage."""
    print("=" * 70)
    print("DEMO 2: Factory Function")
    print("=" * 70)
    
    # Create embedders using factory
    local = create_embedder("local")
    print(f"\nLocal embedder: {type(local).__name__}")
    
    # Custom model
    # custom = create_embedder("local", model="all-mpnet-base-v2")
    # print(f"Custom model embedder: {type(custom).__name__}")
    
    print("\nFactory supports:")
    print("  - backend='local' → LocalEmbedder")
    print("  - backend='openai' → OpenAIEmbedder")
    print("  - model=<name> → Custom model selection")
    print()


def demo_empty_input():
    """Demonstrate empty input handling."""
    print("=" * 70)
    print("DEMO 3: Empty Input Handling")
    print("=" * 70)
    
    embedder = LocalEmbedder()
    result = embedder.embed([])
    
    print(f"\nInput: [] (empty list)")
    print(f"Output shape: {result.shape}")
    print(f"Expected: (0, 384)")
    print()


def demo_openai_embedder():
    """Demonstrate OpenAI embedder (if API key available)."""
    print("=" * 70)
    print("DEMO 4: OpenAI Embedder (Optional)")
    print("=" * 70)
    
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠ OPENAI_API_KEY not set, skipping OpenAI demo")
        print("Set environment variable to enable: export OPENAI_API_KEY=sk-...")
        print()
        return
    
    try:
        embedder = OpenAIEmbedder()
        lines = ["Warning: signal CLK unconnected"]
        embeddings = embedder.embed(lines)
        
        print(f"\nInput: {len(lines)} lines")
        print(f"Output shape: {embeddings.shape}")
        print(f"Expected: ({len(lines)}, 1536) for text-embedding-3-small")
        print()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("VLSI Report Cluster - Embedder Module API Demo")
    print("=" * 70)
    print()
    
    try:
        demo_local_embedder()
        demo_factory_function()
        demo_empty_input()
        demo_openai_embedder()
        
        print("=" * 70)
        print("✓ All demos completed successfully!")
        print("=" * 70)
        print()
        
    except ModuleNotFoundError as e:
        print(f"\n✗ Missing dependency: {e}")
        print("\nInstall dependencies:")
        print("  pip install -e '.[dev]'")
        print("  pip install -e '.[openai]'  # For OpenAI support")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
