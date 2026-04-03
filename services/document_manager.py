"""
Handles document metadata, sharing, and basic upload/download operations.
Uses EncryptedStorage for secure content storage.
"""

import os
import time
import secrets

import config
from services.storage import load_json, save_json
from services.encrypted_storage import EncryptedStorage
from services.user_manager import get_user_from_username
from services.validation import safe_filename


class DocumentManager:
    VALID_SHARE_ROLES = {"viewer", "editor"}

    def __init__(self):
        self.documents_file = config.DOCUMENTS_FILE
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

    def get_user_role_for_doc(self, doc_id, username):
        document = self.get_document_by_id(doc_id)
        if document is None:
            return None

        if document["owner"] == username:
            return "owner"

        shared_with = document.get("shared_with", {})
        info = shared_with.get(username)
        
        if info is None:
            return None

        return info["role"]

    def can_view(self, doc_id, username):
        role = self.get_user_role_for_doc(doc_id, username)
        return role in {"owner", "editor", "viewer"}

    def can_edit(self, doc_id, username):
        role = self.get_user_role_for_doc(doc_id, username)
        return role in {"owner", "editor"}

    def can_share(self, doc_id, username):
        role = self.get_user_role_for_doc(doc_id, username)
        return role in {"owner"}

    def get_user_documents(self, username):
        documents = self.load_documents()
        visible_docs = []

        for doc in documents:
            if doc["owner"] == username:
                visible_docs.append(doc)
                continue

            shared_with = doc.get("shared_with", {})
            if username in shared_with:
                visible_docs.append(doc)

        return visible_docs

    def upload_file(self, username, file):
        try:
            filename = safe_filename(file.filename)
        except ValueError:
            return {"error": "Invalid filename"}
        
        doc_id = self.generate_doc_id()

        encrypted_path = os.path.join(self.docs_dir, f"{doc_id}.enc")

        # read file bytes
        file_bytes = file.read()

        # encrypt and store
        self.storage.save_encrypted(
            encrypted_path,
            {
                "filename": filename,
                "data": file_bytes.decode("latin1")  # store binary safely
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
            "shared_with": {}
        }

        documents = self.load_documents()
        documents.append(document)
        self.save_documents(documents)

        return {
            "success": True,
            "doc_id": doc_id,
            "filename": filename
        }

    def delete_document(self, username, doc_id):
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

    def share_document(self, owner_username, doc_id, target_username, role):
        if role not in self.VALID_SHARE_ROLES:
            return {"error": "Invalid role"}
        
        target_user = get_user_from_username(target_username)
        if target_user is None:
            return {"error": "Target user does not exist"}

        if role == "editor" and target_user.get("role") == "guest":
            return {"error": "Guests cannot be given editor access"}

        documents = self.load_documents()

        for document in documents:
            if document["doc_id"] == doc_id:
                if not self.can_share(doc_id, owner_username):
                    return {"error": "Forbidden"}

                if target_username == owner_username:
                    return {"error": "Owner already has access"}

                shared_with = document.get("shared_with", {})
                shared_with[target_username] = {
                    "role": role,
                    "shared_at": time.time()
                }
                document["shared_with"] = shared_with
                document["updated_at"] = time.time()

                self.save_documents(documents)
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "target_username": target_username,
                    "role": role
                }

        return {"error": "Document not found"}

    def unshare_document(self, owner_username, doc_id, target_username):
        documents = self.load_documents()

        for document in documents:
            if document["doc_id"] == doc_id:
                if document["owner"] != owner_username:
                    return {"error": "Forbidden"}

                if target_username == owner_username:
                    return {"error": "Owner access cannot be removed"}

                shared_with = document.get("shared_with", {})
                if target_username not in shared_with:
                    return {"error": "User does not have shared access"}

                del shared_with[target_username]
                document["shared_with"] = shared_with
                document["updated_at"] = time.time()

                self.save_documents(documents)
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "target_username": target_username
                }

        return {"error": "Document not found"}

    def update_share_role(self, owner_username, doc_id, target_username, new_role):
        if new_role not in self.VALID_SHARE_ROLES:
            return {"error": "Invalid role"}
        
        target_user = get_user_from_username(target_username)
        if target_user is None:
            return {"error": "Target user does not exist"}

        if new_role == "editor" and target_user.get("role") == "guest":
            return {"error": "Guests cannot be given editor access"}

        documents = self.load_documents()

        for document in documents:
            if document["doc_id"] == doc_id:
                if document["owner"] != owner_username:
                    return {"error": "Forbidden"}

                if target_username == owner_username:
                    return {"error": "Owner role cannot be changed"}

                shared_with = document.get("shared_with", {})
                if target_username not in shared_with:
                    return {"error": "User does not have shared access"}

                shared_with[target_username]["role"] = new_role
                document["shared_with"] = shared_with
                document["updated_at"] = time.time()

                self.save_documents(documents)
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "target_username": target_username,
                    "role": new_role
                }

        return {"error": "Document not found"}

    def list_shares_for_doc(self, requesting_username, doc_id):
        document = self.get_document_by_id(doc_id)
        if document is None:
            return {"error": "Document not found"}

        requesting_user = get_user_from_username(requesting_username)
        if requesting_user is None:
            return {"error": "Forbidden"}

        is_admin = requesting_user.get("role") == "admin"
        is_owner = document["owner"] == requesting_username

        if not is_admin and not is_owner:
            return {"error": "Forbidden"}

        share_list = []
        for username, info in document.get("shared_with", {}).items():
            share_list.append({
                "username": username,
                "role": info["role"],
                "shared_at": info["shared_at"]
            })

        return {
            "doc_id": doc_id,
            "owner": document["owner"],
            "shares": share_list
        }
    
    def replace_file(self, username, doc_id, file):
        documents = self.load_documents()

        for document in documents:
            if document["doc_id"] == doc_id:
                if not self.can_edit(doc_id, username):
                    return {"error": "Forbidden"}

                file_bytes = file.read()

                self.storage.save_encrypted(
                    document["encrypted_path"],
                    {
                        "filename": document["filename"],
                        "data": file_bytes.decode("latin1")
                    }
                )

                document["version"] += 1
                document["updated_at"] = time.time()

                self.save_documents(documents)

                return {
                    "success": True,
                    "doc_id": doc_id,
                    "version": document["version"]
                }

        return {"error": "Document not found"}

    def get_file(self, username, user_role, doc_id):
        document = self.get_document_by_id(doc_id)

        if document is None:
            return {"error": "Document not found"}

        if user_role != "admin" and not self.can_view(doc_id, username):
            return {"error": "Forbidden"}

        decrypted = self.storage.load_encrypted(document["encrypted_path"])
        data = decrypted["data"].encode("latin1")

        return {
            "filename": document["filename"],
            "data": data
        }
    
    def downgrade_user_document_access(self, username):
        documents_data = load_json(self.documents_file)
        changed = False

        for doc in documents_data.get("documents", []):
            shared_with = doc.get("shared_with", {})
            if shared_with.get(username) == "editor":
                shared_with[username] = "viewer"
                changed = True

        if changed:
            save_json(self.documents_file, documents_data)

        return changed