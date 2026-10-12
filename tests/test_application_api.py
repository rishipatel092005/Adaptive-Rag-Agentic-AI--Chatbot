"""Offline integration tests for authentication and persisted chat APIs."""

import copy
import io
import os
import unittest
from unittest.mock import patch

import httpx
from docx import Document as WordDocument
from fastapi import FastAPI
from langchain_core.messages import AIMessage
from pymongo.errors import DuplicateKeyError
from starlette.datastructures import UploadFile

from src.api import auth_routes, routes
from src.auth import create_access_token
from src.rag.document_upload import documents as process_document


class InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, records):
        self.records = records

    def sort(self, key, direction):
        self.records.sort(key=lambda item: item.get(key), reverse=direction < 0)
        return self

    async def to_list(self, length):
        return copy.deepcopy(self.records[:length])


class FakeCollection:
    def __init__(self):
        self.records = []
        self.unique_username = False

    async def create_index(self, *args, **kwargs):
        self.unique_username = kwargs.get("unique", False)
        return "test-index"

    async def insert_one(self, record):
        if self.unique_username and any(
            item.get("username") == record.get("username") for item in self.records
        ):
            raise DuplicateKeyError("duplicate username")
        stored = copy.deepcopy(record)
        stored["_id"] = str(len(self.records) + 1)
        self.records.append(stored)
        return InsertResult(stored["_id"])

    async def find_one(self, query, projection=None):
        record = next((item for item in self.records if self._matches(item, query)), None)
        return self._project(record, projection) if record else None

    def find(self, query, projection=None):
        results = [
            self._project(item, projection)
            for item in self.records
            if self._matches(item, query)
        ]
        return FakeCursor(results)

    async def update_one(self, query, update):
        record = next((item for item in self.records if self._matches(item, query)), None)
        if not record:
            return UpdateResult(0)
        record.update(copy.deepcopy(update.get("$set", {})))
        for key, increment in update.get("$inc", {}).items():
            record[key] = record.get(key, 0) + increment
        return UpdateResult(1)

    async def delete_one(self, query):
        for index, record in enumerate(self.records):
            if self._matches(record, query):
                del self.records[index]
                return DeleteResult(1)
        return DeleteResult(0)

    async def delete_many(self, query):
        original_count = len(self.records)
        self.records = [item for item in self.records if not self._matches(item, query)]
        return DeleteResult(original_count - len(self.records))

    @staticmethod
    def _matches(record, query):
        return all(record.get(key) == value for key, value in query.items())

    @staticmethod
    def _project(record, projection):
        result = copy.deepcopy(record)
        if projection:
            for key, include in projection.items():
                if include == 0:
                    result.pop(key, None)
        return result


class ApplicationApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(auth_routes.router)
        self.app.include_router(routes.router)
        self.users = FakeCollection()
        self.conversations = FakeCollection()
        self.messages = FakeCollection()
        self.documents = FakeCollection()
        self.patches = [
            patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key-with-at-least-32-characters"}),
            patch("src.auth.users", self.users),
            patch("src.api.auth_routes.users", self.users),
            patch("src.api.routes.conversations", self.conversations),
            patch("src.api.routes.messages", self.messages),
            patch("src.api.routes.user_documents", self.documents),
            patch("src.api.routes.documents", return_value=True),
            patch.object(
                routes.builder,
                "invoke",
                return_value={
                    "messages": [AIMessage(content="A grounded answer.")],
                    "route": "index",
                    "citations": [{"source": "notes.pdf", "page": 2}],
                },
            ),
        ]
        for context in self.patches:
            context.start()
            self.addCleanup(context.stop)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://test",
        )
        self.addAsyncCleanup(self.client.aclose)

    async def test_registration_login_and_token_validation(self):
        created = await self.client.post(
            "/auth/register",
            json={"username": "alice", "password": "secure-pass-123"},
        )
        self.assertEqual(created.status_code, 201)
        duplicate = await self.client.post(
            "/auth/register",
            json={"username": "alice", "password": "secure-pass-123"},
        )
        self.assertEqual(duplicate.status_code, 409)

        weak_password = await self.client.post(
            "/auth/register",
            json={"username": "bob", "password": "short"},
        )
        self.assertEqual(weak_password.status_code, 422)

        invalid = await self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "incorrect-pass"},
        )
        self.assertEqual(invalid.status_code, 401)

        logged_in = await self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "secure-pass-123"},
        )
        self.assertEqual(logged_in.status_code, 200)
        token = logged_in.json()["access_token"]
        profile = await self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(profile.json()["username"], "alice")

        signed_out = await self.client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(signed_out.status_code, 204)
        revoked = await self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(revoked.status_code, 401)

        expired_or_tampered = await self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}tampered"},
        )
        self.assertEqual(expired_or_tampered.status_code, 401)

    async def test_conversation_chat_ownership_rename_delete_and_upload(self):
        await self.client.post(
            "/auth/register",
            json={"username": "alice", "password": "secure-pass-123"},
        )
        login = await self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "secure-pass-123"},
        )
        alice_token = login.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}

        created = await self.client.post(
            "/conversations",
            json={"title": "New chat"},
            headers=alice_headers,
        )
        self.assertEqual(created.status_code, 201)
        conversation_id = created.json()["id"]
        self.assertNotIn("user_id", created.json())

        reply = await self.client.post(
            "/rag/query",
            json={"conversation_id": conversation_id, "query": "Explain the project."},
            headers=alice_headers,
        )
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json()["content"], "A grounded answer.")
        self.assertEqual(reply.json()["route"], "index")
        self.assertEqual(reply.json()["citations"], [{"source": "notes.pdf", "page": 2}])

        restored = await self.client.get(
            f"/conversations/{conversation_id}",
            headers=alice_headers,
        )
        self.assertEqual([item["type"] for item in restored.json()["messages"]], ["human", "ai"])
        self.assertEqual(restored.json()["messages"][1]["citations"], [{"source": "notes.pdf", "page": 2}])
        listing = await self.client.get("/conversations", headers=alice_headers)
        self.assertEqual(listing.json()[0]["title"], "Explain the project.")
        search_results = await self.client.get(
            "/conversations",
            params={"search": "grounded answer"},
            headers=alice_headers,
        )
        self.assertEqual(len(search_results.json()), 1)
        self.assertNotIn("search_text", search_results.json()[0])

        renamed = await self.client.patch(
            f"/conversations/{conversation_id}",
            json={"title": "Project notes"},
            headers=alice_headers,
        )
        self.assertEqual(renamed.json()["title"], "Project notes")

        await self.client.post(
            "/auth/register",
            json={"username": "bob", "password": "secure-pass-456"},
        )
        bob_login = await self.client.post(
            "/auth/login",
            json={"username": "bob", "password": "secure-pass-456"},
        )
        bob_headers = {"Authorization": f"Bearer {bob_login.json()['access_token']}"}
        forbidden = await self.client.get(
            f"/conversations/{conversation_id}",
            headers=bob_headers,
        )
        self.assertEqual(forbidden.status_code, 404)
        forbidden_query = await self.client.post(
            "/rag/query",
            json={"conversation_id": conversation_id, "query": "Read this chat."},
            headers=bob_headers,
        )
        self.assertEqual(forbidden_query.status_code, 404)

        uploaded = await self.client.post(
            "/rag/documents/upload",
            headers={**alice_headers, "X-Description": "Reference notes"},
            files={"file": ("notes.txt", b"some notes", "text/plain")},
        )
        self.assertEqual(uploaded.status_code, 200)
        docs = await self.client.get("/rag/documents", headers=alice_headers)
        self.assertEqual(docs.json()[0]["filename"], "notes.txt")
        uploaded_docx = await self.client.post(
            "/rag/documents/upload",
            headers={**alice_headers, "X-Description": "Project brief"},
            files={
                "file": (
                    "brief.docx",
                    b"mock docx content",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        self.assertEqual(uploaded_docx.status_code, 200)

        deleted = await self.client.delete(
            f"/conversations/{conversation_id}",
            headers=alice_headers,
        )
        self.assertTrue(deleted.json()["deleted"])
        missing = await self.client.get(
            f"/conversations/{conversation_id}",
            headers=alice_headers,
        )
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(self.messages.records, [])

    async def test_authentication_is_required_and_tokens_expire(self):
        unauthenticated = await self.client.get("/conversations")
        self.assertEqual(unauthenticated.status_code, 401)

        expired = create_access_token("alice")
        with patch("src.auth.time.time", return_value=10**12):
            response = await self.client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {expired}"},
            )
        self.assertEqual(response.status_code, 401)

    async def test_guest_session_opens_without_account_storage(self):
        guest = await self.client.post("/auth/guest")
        self.assertEqual(guest.status_code, 200)
        result = guest.json()
        self.assertEqual(result["username"], "Guest")
        self.assertTrue(result["access_token"])

        profile = await self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {result['access_token']}"},
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["username"], "Guest")
        self.assertTrue(profile.json()["is_guest"])

        ended = await self.client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {result['access_token']}"},
        )
        self.assertEqual(ended.status_code, 204)

    def test_docx_file_is_parsed_and_user_metadata_is_applied(self):
        word = WordDocument()
        word.add_paragraph("A private project brief with several useful facts.")
        data = io.BytesIO()
        word.save(data)
        data.seek(0)
        uploaded = UploadFile(filename="brief.docx", file=data)

        with patch(
            "src.rag.document_upload.retriever_chain",
            side_effect=lambda chunks: chunks,
        ):
            chunks = process_document(
                "Project reference",
                uploaded,
                user_id="alice",
            )

        self.assertEqual(len(chunks), 1)
        self.assertIn("private project brief", chunks[0].page_content)
        self.assertEqual(chunks[0].metadata["source"], "brief.docx")
        self.assertEqual(chunks[0].metadata["user_id"], "alice")


if __name__ == "__main__":
    unittest.main()
