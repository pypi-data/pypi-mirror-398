import requests
import json
from typing import Dict, Any, Optional

class FirestoreClient:
    # Public API Key for demo purposes. In prod, use a proxy or specific CLI client ID.
    API_KEY = "AIzaSyAQUOCeTto6bJ22RfD86vPBi1_SjAh5qEI"

    def __init__(self, project_id: str, token: str):
        self.project_id = project_id
        self.auth_token = token # Renamed to match usage in main.py updates if any, or mapped below
        self.token = token
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"

    def exchange_refresh_token(self, refresh_token: str) -> str:
        """Exchange refresh token for ID token."""
        url = f"https://securetoken.googleapis.com/v1/token?key={self.API_KEY}"
        resp = requests.post(url, json={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        })
        resp.raise_for_status()
        return resp.json()["id_token"]

    def _get_headers(self):
        # Use auth_token if available (updated by refresh), else initial token
        token = getattr(self, 'auth_token', self.token)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _parse_value(self, value: Dict) -> Any:
        if "stringValue" in value:
            return value["stringValue"]
        if "mapValue" in value:
            return self._parse_document(value["mapValue"])
        if "arrayValue" in value:
            return [self._parse_value(v) for v in value["arrayValue"].get("values", [])]
        # Add integerValue, doubleValue, booleanValue as needed
        if "integerValue" in value:
            return int(value["integerValue"])
        return None

    def _parse_document(self, doc: Dict) -> Dict[str, Any]:
        """Converts Firestore REST format to simple dict."""
        fields = doc.get("fields", {})
        result = {}
        for k, v in fields.items():
            result[k] = self._parse_value(v)
        return result

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{collection}/{doc_id}"
        resp = requests.get(url, headers=self._get_headers())
        if resp.status_code == 200:
            return self._parse_document(resp.json())
        if resp.status_code == 404:
            return None
        resp.raise_for_status()

    def list_documents(self, collection: str) -> list:
        url = f"{self.base_url}/{collection}"
        resp = requests.get(url, headers=self._get_headers())
        resp.raise_for_status()
        
        data = resp.json()
        documents = data.get("documents", [])
        return [
            {**self._parse_document(d), "id": d["name"].split("/")[-1]} 
            for d in documents
        ]

    def run_query(self, collection_name: str, query: Dict) -> list:
        """
        Run a structured query against Firestore.
        collection_name: e.g. "organizations" (at root) or "organizations/123/projects"
        """
        # For root collections, url is .../documents:runQuery
        # But for specific path context, it might differ. 
        # The REST API is https://firestore.googleapis.com/v1/{parent=projects/*/databases/*/documents}:runQuery
        # parent = projects/{project_id}/databases/(default)/documents (for root search)
        
        url = f"{self.base_url}:runQuery" 
        
        # We need to specify 'from' in the query if we want to target a specific collection
        # structuredQuery = { from: [{ collectionId: "organizations" }], where: ... }
        
        body = {
            "structuredQuery": query
        }
        
        resp = requests.post(url, headers=self._get_headers(), json=body)
        try:
            resp.raise_for_status()
        except Exception:
            # On 403 or other errors, let's print debug if needed, but raise for now
            raise

        results = []
        for item in resp.json():
            if "document" in item:
                d = item["document"]
                parsed = self._parse_document(d)
                parsed["id"] = d["name"].split("/")[-1]
                # Also store the full path (name) as it's useful for nested resolution
                parsed["_path"] = d["name"].replace(f"projects/{self.project_id}/databases/(default)/documents/", "")
                results.append(parsed)
        return results
