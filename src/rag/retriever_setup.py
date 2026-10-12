"""
Retriever setup and vector store configuration.
"""

import os

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
# from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import FAISS

from src.core.config import settings

embeddings = OpenAIEmbeddings()

# Global variable to store the FAISS vectorstore instance
# This ensures get_retriever() can access documents stored by retriever_chain()
_faiss_vectorstore = None


def retriever_chain(chunks: list[Document]):
    """
    Initialize and store documents in FAISS vector database.

    Args:
        chunks: List of document chunks to store.

    Returns:
        Boolean indicating success of the operation.
    """
    global _faiss_vectorstore

    try:
        # Commenting out Qdrant code for temporary FAISS usage
        # vectorstore = QdrantVectorStore.from_documents(
        #     documents=chunks,
        #     embedding=embeddings,
        #     url=settings.QDRANT_URL,
        #     api_key=settings.QDRANT_API_KEY,
        #     collection_name=settings.CODE_COLLECTION,
        # )
        if _faiss_vectorstore is None:
            _faiss_vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=embeddings,
            )
        else:
            _faiss_vectorstore.add_documents(chunks)

        print("FAISS vector store initialized with documents")
        print(f"Vectorstore contains {len(chunks)} document chunks")
        return True
    except Exception as e:
        print(f"Error storing documents in FAISS: {e}")
        return False


def get_retriever(user_id: str | None = None):
    """
    Get a retriever tool connected to the FAISS vector store.

    Returns the retriever tool that can search documents stored by retriever_chain().
    If no documents have been uploaded yet, creates a retriever with a dummy document.

    Returns:
        A LangChain retriever tool configured for the vector store.

    Raises:
        Exception: If vector store initialization fails.
    """
    global _faiss_vectorstore

    try:
        # Commenting out Qdrant code for temporary FAISS usage
        # vectorstore = QdrantVectorStore.from_documents(
        #     documents=[],
        #     embedding=embeddings,
        #     url=settings.QDRANT_URL,
        #     api_key=settings.QDRANT_API_KEY,
        #     collection_name=settings.CODE_COLLECTION,
        # )
        # retriever = vectorstore.as_retriever()

        # Use the global vectorstore if it exists (documents have been uploaded)
        if _faiss_vectorstore is not None:
            search_kwargs = {"k": 4}
            if user_id is not None:
                search_kwargs["filter"] = {"user_id": user_id}
            retriever = _faiss_vectorstore.as_retriever(search_kwargs=search_kwargs)
            print("Using existing FAISS vectorstore with uploaded documents")
        else:
            # No documents uploaded yet, create dummy for initialization
            print("No documents uploaded yet, creating dummy vectorstore")
            from langchain_core.documents import Document as LangChainDocument

            dummy_doc = LangChainDocument(
                page_content="No documents have been uploaded yet. Please upload a document first.",
                metadata={"source": "initialization"}
            )

            _faiss_vectorstore = FAISS.from_documents(
                documents=[dummy_doc],
                embedding=embeddings
            )
            retriever = _faiss_vectorstore.as_retriever()

        retriever_tool = create_retriever_tool(
            retriever,
            "retriever_customer_uploaded_documents",
            "Use this tool only to answer questions about documents uploaded by the current user."
        )

        return retriever_tool

    except Exception as e:
        print(f"Error initializing retriever: {e}")
        raise Exception(e)
