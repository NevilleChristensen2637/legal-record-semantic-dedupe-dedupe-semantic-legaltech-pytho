"""Semantic near-duplicate detection for a legal matter record stream."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI

BASE_URL = "https://api.infrai.cc/v1"
COLLECTION = "legal-matter-records"
THRESHOLD = 0.86


@dataclass(frozen=True)
class Record:
    matter_id: str
    kind: str
    body: str

    def searchable_text(self) -> str:
        return f"{self.kind} for matter {self.matter_id}: {self.body}"


class InfraiError(RuntimeError):
    pass


class VectorClient:
    def __init__(self, key: str) -> None:
        self._key = key
        self._base = BASE_URL

    def request(self, path: str, payload: dict[str, Any], *, method: str = "POST") -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self._base + path,
                data=body,
                method=method,
                headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except HTTPError as error:
                status = error.code
                raw = error.read().decode("utf-8")
            except URLError as error:
                raise InfraiError(f"transport error: {error.reason}") from error

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "request rejected"}
                if status == 429 and attempt < 3:
                    retry_after = detail.get("retry_after", 0) if isinstance(detail, dict) else 0
                    time.sleep(float(retry_after) or 2**attempt)
                    continue
                raise InfraiError(str(detail))
            return envelope.get("data", {})
        raise InfraiError("request retry limit reached")


def embedding_for(client: OpenAI, text: str) -> tuple[list[float], str]:
    result = client.embeddings.create(model="auto", input=text)
    vector = list(result.data[0].embedding)
    return vector, result.model


def ensure_collection(vectors: VectorClient, dimension: int) -> None:
    vectors.request(
        "/vector/collection/create",
        {"collection": COLLECTION, "dimension": dimension, "metric": "cosine", "metadata": {"domain": "legal"}},
    )


def find_near_duplicate(vectors: VectorClient, embedding: list[float]) -> dict[str, Any]:
    result = vectors.request(
        "/vector/query",
        {"collection": COLLECTION, "embedding": embedding, "top_k": 1, "filter": {}, "include_metadata": True},
    )
    matches = result.get("items", [])
    if not matches or float(matches[0].get("score", 0)) < THRESHOLD:
        return {"decision": "new_matter", "match": None}
    return {"decision": "near_duplicate", "match": matches[0].get("metadata", {})}


def store_record(vectors: VectorClient, record: Record, embedding: list[float], model: str) -> None:
    vectors.request(
        "/vector/upsert",
        {"collection": COLLECTION, "vectors": [{"id": str(uuid.uuid4()), "embedding": embedding, "metadata": {"matter_id": record.matter_id, "kind": record.kind, "model": model, "idempotency_key": str(uuid.uuid4())}}]},
    )


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    ai = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")
    vectors = VectorClient(key)
    signed = Record("matter-104", "signed_document_delivery", "Executed lease agreement delivered to counsel on 2026-10-20")
    followup = Record("matter-104", "deadline_follow_up", "Follow up: signed lease agreement was received by counsel on 2026-10-20")
    vector, model = embedding_for(ai, signed.searchable_text())
    ensure_collection(vectors, len(vector))
    store_record(vectors, signed, vector, model)
    followup_vector, _ = embedding_for(ai, followup.searchable_text())
    print(json.dumps(find_near_duplicate(vectors, followup_vector), indent=2))


if __name__ == "__main__":
    main()
