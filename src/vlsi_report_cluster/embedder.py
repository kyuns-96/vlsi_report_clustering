"""Embedder module for text embedding.

This module provides a pluggable embedding engine with:
- Protocol interface for embedders
- LocalEmbedder using sentence-transformers (default)
- OpenAIEmbedder using OpenAI API (optional)
- Factory function to create embedders
"""

import os
from typing import Protocol
import numpy as np
from numpy.typing import NDArray


class Embedder(Protocol):
    """Protocol defining the interface for text embedding implementations.
    
    All embedder implementations must provide an embed method that converts
    text lines to numerical vector representations.
    """
    
    def embed(self, lines: list[str]) -> NDArray[np.float32]:
        """Convert text lines to embeddings.
        
        Args:
            lines: List of text strings to embed
            
        Returns:
            Numpy array of shape (n, embedding_dim) where n is the number of lines
        """
        ...


class LocalEmbedder:
    """Local embedder using sentence-transformers library.
    
    Uses the all-MiniLM-L6-v2 model by default, which produces 384-dimensional
    embeddings. Model is downloaded on first use (~90MB).
    
    Args:
        model: Model name to use (default: "all-MiniLM-L6-v2")
    """
    
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """Initialize LocalEmbedder with specified model.
        
        Raises:
            OSError: If model download fails (check internet connection)
        """
        from sentence_transformers import SentenceTransformer
        try:
            self.model = SentenceTransformer(model)
        except OSError as e:
            raise OSError(
                f"Failed to load model '{model}'. "
                f"Check internet connection for first-time download (~90MB). "
                f"Error: {e}"
            ) from e
    
    def embed(self, lines: list[str]) -> NDArray[np.float32]:
        """Convert text lines to embeddings using sentence-transformers.
        
        Args:
            lines: List of text strings to embed
            
        Returns:
            Numpy array of shape (n, 384) for default model
        """
        if not lines:
            return np.array([], dtype=np.float32).reshape(0, 384)
        
        embeddings = self.model.encode(lines, convert_to_numpy=True)
        return embeddings.astype(np.float32)


class OpenAIEmbedder:
    """OpenAI embedder using OpenAI API.
    
    Uses the text-embedding-3-small model by default. Requires OPENAI_API_KEY
    environment variable to be set.
    
    Args:
        model: Model name to use (default: "text-embedding-3-small")
    """
    
    def __init__(self, model: str = "text-embedding-3-small", base_url: str | None = None):
        """Initialize OpenAIEmbedder with specified model.
        
        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        from openai import OpenAI
        resolved_base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        if resolved_base_url:
            self.client = OpenAI(api_key=api_key, base_url=resolved_base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def embed(self, lines: list[str]) -> NDArray[np.float32]:
        """Convert text lines to embeddings using OpenAI API.
        
        Args:
            lines: List of text strings to embed
            
        Returns:
            Numpy array of shape (n, embedding_dim) where embedding_dim depends on model
        """
        if not lines:
            # text-embedding-3-small produces 1536-dimensional embeddings
            return np.array([], dtype=np.float32).reshape(0, 1536)
        
        response = self.client.embeddings.create(
            input=lines,
            model=self.model
        )
        
        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings, dtype=np.float32)


def create_embedder(
    backend: str = "local",
    model: str | None = None,
    openai_base_url: str | None = None,
) -> Embedder:
    """Factory function to create embedder instances.
    
    Args:
        backend: Embedder backend to use ("local" or "openai")
        model: Model name to use (default depends on backend)
        
    Returns:
        Embedder instance
        
    Raises:
        ValueError: If backend is not recognized
    """
    if backend == "local":
        if model is not None:
            return LocalEmbedder(model=model)
        return LocalEmbedder()
    elif backend == "openai":
        if model is not None:
            return OpenAIEmbedder(model=model, base_url=openai_base_url)
        return OpenAIEmbedder(base_url=openai_base_url)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'local' or 'openai'")
