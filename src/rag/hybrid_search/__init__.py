"""
Hybrid retrieval package.

Combines:
- Dense vector retrieval
- BM25 keyword retrieval
- Reciprocal Rank Fusion (RRF)
"""

from .hybrid_retriever import HybridRetriever, hybrid_search

__all__ = [
    "HybridRetriever",
    "hybrid_search",
]