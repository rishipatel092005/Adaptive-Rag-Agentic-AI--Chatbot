"""Authenticated RAG, document, and conversation endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from langchain_core.messages import AIMessage, HumanMessage
from starlette.concurrency import run_in_threadpool

from src.auth import get_current_user
from src.db.mongo_client import db
from src.models.conversation import ChatQuery, ConversationCreate, ConversationRename
from src.rag.document_upload import documents
from src.rag.graph_builder import builder

router = APIRouter()
conversations = db["conversations"]
messages = db["chat_history"]
user_documents = db["user_documents"]


def _serialize_conversation(document: dict) -> dict:
    document.pop("user_id", None)
    document.pop("search_text", None)
    document["created_at"] = document["created_at"].isoformat()
    document["updated_at"] = document["updated_at"].isoformat()
    return document


@router.post("/conversations", status_code=201)
async def create_conversation(
    request: ConversationCreate,
    user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    conversation = {
        "id": str(uuid4()),
        "user_id": user["username"],
        "title": request.title.strip() or "New chat",
        "search_text": "",
        "created_at": now,
        "updated_at": now,
    }
    try:
        await conversations.insert_one(conversation)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; conversations cannot be loaded until storage is configured.",
        ) from exc
    return _serialize_conversation(conversation)


@router.get("/conversations")
async def list_conversations(
    search: str = Query(default="", max_length=100),
    user: dict = Depends(get_current_user),
):
    try:
        records = await conversations.find(
            {"user_id": user["username"]},
            {"_id": 0, "user_id": 0},
        ).sort("updated_at", -1).to_list(length=200)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; conversations cannot be loaded until storage is configured.",
        ) from exc
    normalized_search = search.strip().casefold()
    if normalized_search:
        records = [
            record
            for record in records
            if normalized_search in record.get("title", "").casefold()
            or normalized_search in record.get("search_text", "").casefold()
        ]
    return [_serialize_conversation(record) for record in records]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    try:
        conversation = await conversations.find_one(
            {"id": conversation_id, "user_id": user["username"]},
            {"_id": 0},
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        history = await messages.find(
            {"conversation_id": conversation_id, "user_id": user["username"]},
            {"_id": 0, "user_id": 0},
        ).sort("timestamp", 1).to_list(length=2000)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; conversations cannot be updated until storage is configured.",
        ) from exc
    conversation = _serialize_conversation(conversation)
    for message in history:
        message["timestamp"] = message["timestamp"].isoformat()
    conversation["messages"] = history
    return conversation


@router.patch("/conversations/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    request: ConversationRename,
    user: dict = Depends(get_current_user),
):
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="A conversation title is required.")
    try:
        result = await conversations.update_one(
            {"id": conversation_id, "user_id": user["username"]},
            {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; conversations cannot be deleted until storage is configured.",
        ) from exc
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"id": conversation_id, "title": title}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    owner_query = {"id": conversation_id, "user_id": user["username"]}
    try:
        result = await conversations.delete_one(owner_query)
        if not result.deleted_count:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        await messages.delete_many(
            {"conversation_id": conversation_id, "user_id": user["username"]}
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Conversation storage is unavailable.") from exc
    return {"deleted": True}


@router.post("/rag/query")
async def rag_query(
    request: ChatQuery,
    user: dict = Depends(get_current_user),
):
    username = user["username"]
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=422, detail="Enter a question before sending.")
    owner_query = {
        "id": request.conversation_id,
        "user_id": username,
    }
    try:
        conversation = await conversations.find_one(owner_query)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        inserted = await messages.insert_one(
            {
                "conversation_id": request.conversation_id,
                "user_id": username,
                "type": "human",
                "content": query_text,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        history = await messages.find(
            {"conversation_id": request.conversation_id, "user_id": username},
            {"_id": 0, "type": 1, "content": 1, "additional_kwargs": 1},
        ).sort("timestamp", 1).to_list(length=2000)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; chat history cannot be saved until storage is configured.",
        ) from exc

    langchain_messages = []
    for message in history:
        message_type = message.get("type")
        message_class = HumanMessage if message_type in ("human", "user") else AIMessage
        langchain_messages.append(
            message_class(
                content=message.get("content", ""),
                additional_kwargs=message.get("additional_kwargs", {}),
            )
        )

    try:
        result = await run_in_threadpool(
            builder.invoke,
            {"messages": langchain_messages, "user_id": username},
        )
        last_message = result["messages"][-1]
        content = last_message.content
        if not isinstance(content, str):
            content = str(content)
        route = result.get("route")
        citations = result.get("citations") or []
        await messages.insert_one(
            {
                "conversation_id": request.conversation_id,
                "user_id": username,
                "type": "ai",
                "content": content,
                "route": route,
                "citations": citations,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        now = datetime.now(timezone.utc)
        title = conversation["title"]
        if title == "New chat":
            title = query_text.splitlines()[0][:60]
        search_text = " ".join(
            filter(None, [conversation.get("search_text", ""), query_text, content])
        )[-10000:]
        await conversations.update_one(
            owner_query,
            {
                "$set": {
                    "title": title,
                    "search_text": search_text,
                    "updated_at": now,
                }
            },
        )
    except Exception as exc:
        await messages.delete_one({"_id": inserted.inserted_id})
        raise HTTPException(status_code=502, detail="The RAG workflow could not complete this request.") from exc

    return {"content": content, "route": route, "citations": citations}


@router.post("/rag/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description"),
    user: dict = Depends(get_current_user),
):
    filename = file.filename or ""
    if not filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported.",
        )
    if not description.strip():
        raise HTTPException(status_code=422, detail="A document description is required.")
    try:
        status = await run_in_threadpool(documents, description.strip(), file, user["username"])
        if not status:
            raise HTTPException(status_code=502, detail="The document could not be indexed.")
        record = {
            "id": str(uuid4()),
            "user_id": user["username"],
            "filename": filename,
            "description": description.strip(),
            "status": "ready",
            "uploaded_at": datetime.now(timezone.utc),
        }
        await user_documents.insert_one(record)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Document processing failed.") from exc
    return {
        "id": record["id"],
        "filename": filename,
        "status": "ready",
        "uploaded_at": record["uploaded_at"].isoformat(),
    }


@router.get("/rag/documents")
async def list_documents(user: dict = Depends(get_current_user)):
    try:
        records = await user_documents.find(
            {"user_id": user["username"]},
            {"_id": 0, "user_id": 0},
        ).sort("uploaded_at", -1).to_list(length=200)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable; document status cannot be loaded until storage is configured.",
        ) from exc
    for record in records:
        record["uploaded_at"] = record["uploaded_at"].isoformat()
    return records
