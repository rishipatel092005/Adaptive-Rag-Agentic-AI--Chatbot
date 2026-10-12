"""
Document upload and processing module.
"""

import os
import tempfile

from fastapi import File, HTTPException, UploadFile
from docx import Document as WordDocument
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.retriever_setup import retriever_chain


def documents(
    description: str,
    file: UploadFile = File(...),
    user_id: str | None = None,
):
    """
    Process and upload a document for RAG.

    Validates file type, loads content, chunks documents,
    and stores them in the vector database.

    Args:
        description: User-provided document description.
        file: The uploaded file (PDF or TXT).

    Returns:
        Boolean indicating success of the upload process.

    Raises:
        HTTPException: If file type is not supported or loading fails.
    """
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()
    if extension not in (".pdf", ".txt", ".docx"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported."
        )

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    ) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    try:
        if extension == ".pdf":
            docs = PyPDFLoader(tmp_path).load()
        elif extension == ".txt":
            docs = TextLoader(tmp_path, encoding="utf-8").load()
        else:
            word_document = WordDocument(tmp_path)
            content = "\n".join(
                paragraph.text
                for paragraph in word_document.paragraphs
                if paragraph.text.strip()
            )
            if not content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="The DOCX document does not contain readable paragraph text.",
                )
            docs = [Document(page_content=content, metadata={"source": filename})]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded document could not be parsed.",
        ) from exc
    finally:
        os.unlink(tmp_path)

    # Split documents into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        chunk.metadata["source"] = filename
        chunk.metadata["description"] = description
        if user_id is not None:
            chunk.metadata["user_id"] = user_id

    return retriever_chain(chunks)

