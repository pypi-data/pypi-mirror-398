"""Firestore REST stubs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

API_KEY = os.environ.get("NEXT_PUBLIC_FIREBASE_API_KEY", "")

@dataclass
class VaultClient:
    """REST client for Firestore interactions."""
    
    auth_token: Optional[str] = None # ID Token
    base_url: str = "https://firestore.googleapis.com/v1/projects"
    # We need the project ID. For now, assume it's passed or env var.
    project_id: str = "lockbox-45257" # From config

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def exchange_refresh_token(self, refresh_token: str) -> str:
        """Exchange refresh token for ID token."""
        # https://firebase.google.com/docs/reference/rest/auth/#section-refresh-token
        api_key = API_KEY or "YOUR_API_KEY" # Should be injected
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        resp = requests.post(url, json={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        })
        resp.raise_for_status()
        return resp.json()["id_token"]

    def fetch_user_key(self, uid: str) -> Dict[str, Any] | None:
        path = f"{self.project_id}/databases/(default)/documents/users/{uid}"
        try:
            data = self._request(path)
            fields = data.get("fields", {})
            return {
                "publicKey": fields.get("publicKey", {}).get("stringValue"),
                "encryptedPrivateKey": {
                    "salt": fields.get("encryptedPrivateKey", {}).get("mapValue", {}).get("fields", {}).get("salt", {}).get("stringValue"),
                    "nonce": fields.get("encryptedPrivateKey", {}).get("mapValue", {}).get("fields", {}).get("nonce", {}).get("stringValue"),
                    "ciphertext": fields.get("encryptedPrivateKey", {}).get("mapValue", {}).get("fields", {}).get("ciphertext", {}).get("stringValue"),
                }
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def fetch_project_key_envelope(self, project_id: str, uid: str) -> Dict[str, Any] | None:
        # projects/{projectId}/keys/{userId}
        path = f"{self.project_id}/databases/(default)/documents/projects/{project_id}/keys/{uid}"
        try:
            data = self._request(path)
            fields = data.get("fields", {})
            return {
                "nonce": fields.get("nonce", {}).get("stringValue"),
                "ciphertext": fields.get("ciphertext", {}).get("stringValue"),
                "ephemeralPublicKey": fields.get("ephemeralPublicKey", {}).get("stringValue"),
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def fetch_secrets(self, project_id: str) -> Dict[str, Any]:
        path = f"{self.project_id}/databases/(default)/documents/projects/{project_id}/secrets"
        try:
            data = self._request(path)
            secrets = {}
            for doc in data.get("documents", []):
                name = doc["name"].split("/")[-1]
                fields = doc.get("fields", {})
                secrets[name] = {
                    "nonce": fields.get("nonce", {}).get("stringValue"),
                    "ciphertext": fields.get("ciphertext", {}).get("stringValue"),
                }
            return secrets
        except requests.HTTPError as e:
            return {}

    def _request(self, path: str, method: str = "GET", body: Any = None) -> Any:
        url = f"{self.base_url}/{path}"
        response = requests.request(
            method, url, headers=self._headers(), json=body, timeout=10
        )
        response.raise_for_status()
        return response.json()
