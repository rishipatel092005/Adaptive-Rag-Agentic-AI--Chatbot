"""
Cross-encoder reranking using FlashRank.

Pipeline:

Hybrid Search
    ↓
Candidate Documents
    ↓
FlashRank Cross-Encoder
    ↓
Best Documents
"""

from typing import Any

from flashrank import Ranker, RerankRequest
from langchain_core.documents import Document


# --------------------------------------------------
# FlashRank model
# --------------------------------------------------

ranker = Ranker(
    model_name="ms-marco-MiniLM-L-12-v2",
)


def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int = 5,
) -> list[Document]:
    """
    Rerank documents using a cross-encoder.

    Args:
        query:
            User's original question.

        documents:
            Candidate documents returned by Hybrid Search.

        top_k:
            Number of documents to keep after reranking.

    Returns:
        Reranked list of LangChain Documents.
    """

    if not query or not query.strip():
        return []

    if not documents:
        return []

    # Don't request more documents than we actually have.
    top_k = min(top_k, len(documents))

    # --------------------------------------------------
    # Convert LangChain Documents → FlashRank passages
    # --------------------------------------------------

    passages: list[dict[str, Any]] = []

    for index, document in enumerate(documents):

        passages.append(
            {
                "id": str(index),
                "text": document.page_content,
                "meta": {
                    "original_index": index,
                    "metadata": document.metadata,
                },
            }
        )

    # --------------------------------------------------
    # Create reranking request
    # --------------------------------------------------

    request = RerankRequest(
        query=query,
        passages=passages,
    )

    # --------------------------------------------------
    # Run Cross-Encoder
    # --------------------------------------------------

    results = ranker.rerank(request)

    # --------------------------------------------------
    # Convert results back to LangChain Documents
    # --------------------------------------------------

    reranked_documents: list[Document] = []

    for result in results[:top_k]:

        original_index = int(
            result["meta"]["original_index"]
        )

        original_document = documents[
            original_index
        ]

        # Copy metadata so we don't mutate the original.
        metadata = dict(
            original_document.metadata
        )

        # Store reranking score for debugging/evaluation.
        metadata["rerank_score"] = float(
            result["score"]
        )

        reranked_documents.append(
            Document(
                page_content=original_document.page_content,
                metadata=metadata,
            )
        )

    return reranked_documents