"""
BM25 indexing and keyword retrieval.
"""

import re
from typing import Optional

import numpy as np
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


# Global BM25 state.
# This follows the same in-memory architecture your current FAISS setup uses.
_bm25_index: Optional[BM25Okapi] = None
_bm25_documents: list[Document] = []


def tokenize(text: str) -> list[str]:
    """
    Convert text into simple lowercase word tokens.

    Example:
        "Wireless Earbuds for Travel"
        -> ["wireless", "earbuds", "for", "travel"]
    """
    if not text:
        return []

    return re.findall(r"\b\w+\b", text.lower())


def build_bm25_index(documents: list[Document]) -> bool:
    """
    Build the BM25 index from document chunks.

    Args:
        documents: Document chunks to index.

    Returns:
        True when indexing succeeds.
    """
    global _bm25_index
    global _bm25_documents

    if not documents:
        _bm25_index = None
        _bm25_documents = []
        return False

    try:
        tokenized_documents = [
            tokenize(document.page_content)
            for document in documents
        ]

        _bm25_index = BM25Okapi(tokenized_documents)
        _bm25_documents = list(documents)

        print(
            f"BM25 index initialized with "
            f"{len(_bm25_documents)} document chunks"
        )

        return True

    except Exception as exc:
        _bm25_index = None
        _bm25_documents = []
        print(f"Error building BM25 index: {exc}")
        return False


def bm25_search(
    query: str,
    top_k: int = 10,
) -> list[Document]:
    """
    Search the BM25 index.

    Args:
        query: User's search query.
        top_k: Number of documents to return.

    Returns:
        Ranked list of Documents.
    """
    if _bm25_index is None or not _bm25_documents:
        return []

    if not query or not query.strip():
        return []

    top_k = max(1, min(top_k, len(_bm25_documents)))

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scores = np.asarray(
        _bm25_index.get_scores(query_tokens)
    )

    ranked_indices = np.argsort(scores)[::-1][:top_k]

    return [
        _bm25_documents[int(index)]
        for index in ranked_indices
    ]


def clear_bm25_index() -> None:
    """
    Clear the current BM25 index.
    """
    global _bm25_index
    global _bm25_documents

    _bm25_index = None
    _bm25_documents = []


def has_bm25_index() -> bool:
    """
    Check whether a BM25 index is available.
    """
    return _bm25_index is not None and bool(_bm25_documents)