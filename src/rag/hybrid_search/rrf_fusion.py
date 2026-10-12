"""
Reciprocal Rank Fusion (RRF) for combining ranked retrieval results.
"""

from collections import defaultdict
import hashlib
import json

from langchain_core.documents import Document


def _document_key(document: Document) -> str:
    """
    Create a stable identifier for a document.

    We prefer useful metadata such as chunk_id/source/page.
    If that is unavailable, we hash the document content + metadata.
    """

    metadata = document.metadata or {}

    preferred_fields = [
        "chunk_id",
        "id",
        "source",
        "file_name",
        "page",
    ]

    metadata_values = [
        str(metadata[field])
        for field in preferred_fields
        if field in metadata
    ]

    if metadata_values:
        return "|".join(metadata_values)

    raw_value = (
        document.page_content
        + "|"
        + json.dumps(
            metadata,
            sort_keys=True,
            default=str,
        )
    )

    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()


def reciprocal_rank_fusion(
    result_lists: list[list[Document]],
    k: int = 60,
    top_k: int | None = None,
) -> list[tuple[Document, float]]:
    """
    Combine multiple ranked result lists using RRF.

    Formula:

        RRF(d) = Σ 1 / (k + rank)

    Args:
        result_lists:
            Multiple ranked document lists.
        k:
            RRF constant. Common value is 60.
        top_k:
            Optional number of final documents.

    Returns:
        List of:
            (Document, RRF score)
    """

    scores: dict[str, float] = defaultdict(float)
    documents: dict[str, Document] = {}

    for result_list in result_lists:

        for rank, document in enumerate(
            result_list,
            start=1,
        ):
            key = _document_key(document)

            documents[key] = document

            scores[key] += 1.0 / (k + rank)

    ranked_keys = sorted(
        scores.keys(),
        key=lambda key: scores[key],
        reverse=True,
    )

    if top_k is not None:
        ranked_keys = ranked_keys[:top_k]

    return [
        (
            documents[key],
            float(scores[key]),
        )
        for key in ranked_keys
    ]