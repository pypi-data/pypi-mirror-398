"""Service token helpers."""

from __future__ import annotations

import base64
import json
from typing import TypedDict

from .crypto import EnvelopedProjectKey


class ServiceToken(TypedDict):
    version: str
    project_id: str
    bot_public_key: str
    wrapped_key: str


TOKEN_VERSION = "v1"


def encode_service_token(token: ServiceToken) -> str:
    return ".".join(
        [
            TOKEN_VERSION,
            token["project_id"],
            token["bot_public_key"],
            token["wrapped_key"],
        ]
    )


def decode_service_token(token: str) -> ServiceToken:
    parts = token.split(".")
    if len(parts) != 4 or parts[0] != TOKEN_VERSION:
        raise ValueError("Invalid LOCKBOX_TOKEN")
    _, project_id, bot_public_key, wrapped_key = parts
    return {
        "version": TOKEN_VERSION,
        "project_id": project_id,
        "bot_public_key": bot_public_key,
        "wrapped_key": wrapped_key,
    }


def decode_wrapped_key(encoded: str) -> EnvelopedProjectKey:
    """Decode a wrapped project key (base64 of JSON envelope)."""
    raw = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    return json.loads(raw)

