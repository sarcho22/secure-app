"""
Handles document metadata and basic upload/download operations.
Uses EncryptedStorage for secure content storage.
"""

import os
import time
import secrets

import config
from services.storage import load_json, save_json
from services.encrypted_storage import EncryptedStorage


class DocumentManager:
    def __init__(self):
        self.documents_file = os.path.join(config.DATA_DIR, "documents.json")
        self.docs_dir = os.path.join(config.DATA_DIR, "docs")
        self.storage = EncryptedStorage()

        os.makedirs(self.docs_dir, exist_ok=True)

    def load_documents(self):
        data = load_json(self.documents_file)
        return data.get("documents", [])

    def save_documents(self, documents):
        save_json(self.documents_file, {"documents": documents})

    def generate_doc_id(self):
        return secrets.token_urlsafe(16)

    def get_document_by_id(self, doc_id):
        documents = self.load_documents()
        for document in documents:
            if document["doc_id"] == doc_id:
                return document
        return None

    def get_user_documents(self, username):
        documents = self.load_documents()
        return [doc for doc in documents if doc["owner"] == username]

    def upload_document(self, username, filename, content):
        """
        Creates a new encrypted document owned by the given user.
        content should be text for now.
        """
        doc_id = self.generate_doc_id()
        encrypted_path = os.path.join(self.docs_dir, f"{doc_id}.enc")

        self.storage.save_encrypted(
            encrypted_path,
            {
                "content": content
            }
        )

        document = {
            "doc_id": doc_id,
            "owner": username,
            "filename": filename,
            "encrypted_path": encrypted_path,
            "version": 1,
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        documents = self.load_documents()
        documents.append(document)
        self.save_documents(documents)

        return {
            "success": True,
            "doc_id": doc_id,
            "filename": filename
        }

    def download_document(self, username, doc_id):
        """
        For now, only the owner can download.
        Later this will expand to shared users / roles.
        """
        document = self.get_document_by_id(doc_id)
        if document is None:
            return {"error": "Document not found"}

        if document["owner"] != username:
            return {"error": "Forbidden"}

        decrypted_data = self.storage.load_encrypted(document["encrypted_path"])

        return {
            "success": True,
            "doc_id": document["doc_id"],
            "filename": document["filename"],
            "content": decrypted_data.get("content", ""),
            "version": document["version"],
        }

    def delete_document(self, username, doc_id):
        """
        For now, only the owner can delete.
        """
        documents = self.load_documents()
        document = self.get_document_by_id(doc_id)

        if document is None:
            return {"error": "Document not found"}

        if document["owner"] != username:
            return {"error": "Forbidden"}

        if os.path.exists(document["encrypted_path"]):
            os.remove(document["encrypted_path"])

        updated_documents = [doc for doc in documents if doc["doc_id"] != doc_id]
        self.save_documents(updated_documents)

        return {"success": True}