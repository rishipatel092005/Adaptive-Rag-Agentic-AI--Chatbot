"""
Hybrid retriever.

Combines:
    Dense vector retrieval
    +
    BM25 keyword retrieval
    +
    Reciprocal Rank Fusion
"""

from typing import Any

from langchain_core.documents import Document

from src.rag.hybrid.bm25_setup import bm25_search
from src.rag.hybrid.rrf_fusion import reciprocal_rank_fusion
from src.rag.retriever_setup import vector_search


class HybridRetriever:
    """
    Hybrid retriever combining dense and lexical retrieval.
    """

    def __init__(
        self,
        candidate_k: int = 10,
        top_k: int = 5,
        rrf_k: int = 60,
    ) -> None:

        self.candidate_k = max(1, candidate_k)
        self.top_k = max(1, top_k)
        self.rrf_k = max(1, rrf_k)

    def retrieve(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """
        Run dense + BM25 retrieval and fuse results.

        Returns:
            List of dictionaries containing:
                document
                score
                source
        """

        if not query or not query.strip():
            return []

        dense_results = vector_search(
            query=query,
            top_k=self.candidate_k,
        )

        bm25_results = bm25_search(
            query=query,
            top_k=self.candidate_k,
        )

        fused_results = reciprocal_rank_fusion(
            result_lists=[
                dense_results,
                bm25_results,
            ],
            k=self.rrf_k,
            top_k=self.top_k,
        )

        results: list[dict[str, Any]] = []

        for rank, (document, score) in enumerate(
            fused_results,
            start=1,
        ):
            results.append(
                {
                    "document": document,
                    "score": score,
                    "rank": rank,
                }
            )

        return results

    def invoke(
        self,
        query: str,
        config: dict | None = None,
    ) -> list[Document]:
        """
        LangChain-style invoke method.

        Returns only Documents so it is easy to use
        inside the LangGraph nodes.
        """

        del config  # Not needed currently.

        results = self.retrieve(query)

        return [
            item["document"]
            for item in results
        ]


# Shared retriever instance.
hybrid_retriever = HybridRetriever(
    candidate_k=10,
    top_k=5,
    rrf_k=60,
)


def hybrid_search(
    query: str,
    top_k: int = 5,
    candidate_k: int = 10,
) -> list[Document]:
    """
    Convenience function for Hybrid Search.
    """

    retriever = HybridRetriever(
        candidate_k=candidate_k,
        top_k=top_k,
        rrf_k=60,
    )

    return retriever.invoke(query)