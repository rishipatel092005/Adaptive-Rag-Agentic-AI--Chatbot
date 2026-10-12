"""
Retriever setup and vector store configuration.

Dense retrieval:
    FAISS + SentenceTransformer

Sparse retrieval:
    BM25

Hybrid retrieval:
    src.rag.hybrid
"""

import os
from typing import Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.tools import create_retriever_tool
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from src.rag.hybrid.bm25_setup import (
    build_bm25_index,
)


class LocalSentenceTransformerEmbeddings(Embeddings):
    """
    LangChain-compatible wrapper around SentenceTransformer.
    """

    _model: Optional[SentenceTransformer] = None

    model_name = "all-MiniLM-L6-v2"

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        """
        Load the embedding model lazily.
        """

        if cls._model is None:
            print(
                f"Loading embedding model: {cls.model_name}"
            )

            cls._model = SentenceTransformer(
                cls.model_name
            )

            print("Embedding model loaded successfully")

        return cls._model

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """

        if not texts:
            return []

        model = self._get_model()

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for a query.
        """

        if not text:
            return []

        model = self._get_model()

        embedding = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()


# Shared embedding object.
embeddings = LocalSentenceTransformerEmbeddings()


# Global FAISS vectorstore.
_faiss_vectorstore: Optional[FAISS] = None

# Whether real user documents have been indexed.
_has_real_documents = False


def retriever_chain(
    chunks: list[Document],
) -> bool:
    """
    Build the dense FAISS index and BM25 index.

    Args:
        chunks:
            Document chunks produced by document_upload.py.

    Returns:
        True if successful, otherwise False.
    """

    global _faiss_vectorstore
    global _has_real_documents

    if not chunks:
        print("No document chunks were provided.")
        return False

    try:

        print(
            f"Creating FAISS index from {len(chunks)} chunks..."
        )

        # -----------------------------
        # Dense vector index
        # -----------------------------

        _faiss_vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings,
        )

        # -----------------------------
        # BM25 sparse index
        # -----------------------------

        bm25_created = build_bm25_index(chunks)

        if not bm25_created:
            print("Warning: BM25 index could not be created.")
            return False

        _has_real_documents = True

        print(
            "Dense FAISS + BM25 hybrid indexes "
            "initialized successfully."
        )

        print(
            f"Indexed {len(chunks)} document chunks."
        )

        return True

    except Exception as exc:

        _faiss_vectorstore = None
        _has_real_documents = False

        print(
            f"Error storing documents in retrieval indexes: {exc}"
        )

        return False


def vector_search(
    query: str,
    top_k: int = 10,
) -> list[Document]:
    """
    Perform dense vector retrieval using FAISS.

    Args:
        query:
            User's question.

        top_k:
            Number of documents to retrieve.

    Returns:
        Ranked list of Documents.
    """

    if (
        _faiss_vectorstore is None
        or not _has_real_documents
    ):
        return []

    if not query or not query.strip():
        return []

    try:

        documents = _faiss_vectorstore.similarity_search(
            query,
            k=max(1, top_k),
        )

        return documents

    except Exception as exc:

        print(
            f"Error during vector search: {exc}"
        )

        return []


def get_retriever():
    """
    Return a LangChain retriever tool.

    Kept for compatibility with the existing ReAct agent.
    """

    global _faiss_vectorstore

    try:

        if (
            _faiss_vectorstore is not None
            and _has_real_documents
        ):

            retriever = _faiss_vectorstore.as_retriever(
                search_kwargs={
                    "k": 5,
                }
            )

        else:

            # Compatibility fallback for startup.
            dummy_doc = Document(
                page_content=(
                    "No documents have been uploaded yet. "
                    "Please upload a document first."
                ),
                metadata={
                    "source": "initialization"
                },
            )

            dummy_vectorstore = FAISS.from_documents(
                documents=[dummy_doc],
                embedding=embeddings,
            )

            retriever = dummy_vectorstore.as_retriever(
                search_kwargs={
                    "k": 1,
                }
            )

        if os.path.exists("description.txt"):

            with open(
                "description.txt",
                "r",
                encoding="utf-8",
            ) as file:

                description = file.read()

        else:

            description = (
                "the user's uploaded documents"
            )

        retriever_tool = create_retriever_tool(
            retriever,
            "retriever_customer_uploaded_documents",
            (
                f"Use this tool only to answer questions "
                f"about: {description}. "
                "Do not use this tool for unrelated questions."
            ),
        )

        return retriever_tool

    except Exception as exc:

        print(
            f"Error initializing retriever tool: {exc}"
        )

        raise


def clear_retriever_indexes() -> None:
    """
    Clear the current FAISS index.

    Useful during testing or document replacement.
    """

    global _faiss_vectorstore
    global _has_real_documents

    _faiss_vectorstore = None
    _has_real_documents = False