from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Optional, Sequence
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class EmbeddingError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingHTTPError(EmbeddingError):
    url: str
    status_code: int
    body: str

    def __str__(self) -> str:  # pragma: no cover
        msg = f"Embedding request failed ({self.status_code}) at {self.url}"
        if self.body:
            msg += f": {self.body}"
        return msg


def _post_json(url: str, payload: Any, *, timeout_s: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise EmbeddingHTTPError(url=url, status_code=int(getattr(e, "code", 0) or 0), body=err_body) from e
    except (URLError, socket.timeout) as e:
        raise EmbeddingError(f"Embedding request failed at {url}: {e}") from e

    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        preview = raw[:200].decode("utf-8", errors="replace")
        raise EmbeddingError(f"Invalid JSON from embedding server at {url}: {preview}") from e


def _as_vector(obj: Any) -> list[float]:
    if not isinstance(obj, list):
        raise EmbeddingError("Embedding is not a list.")
    try:
        return [float(x) for x in obj]
    except Exception as e:
        raise EmbeddingError("Embedding contains non-numeric values.") from e


def _parse_openai_embeddings(resp: Any, *, expected: int) -> list[list[float]]:
    if not isinstance(resp, dict):
        raise EmbeddingError("OpenAI embeddings response is not a JSON object.")

    data = resp.get("data")
    if not isinstance(data, list):
        raise EmbeddingError("OpenAI embeddings response missing 'data' list.")

    # Prefer explicit indices if present; fall back to positional order.
    by_index: dict[int, list[float]] = {}
    positional: list[list[float]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        emb = _as_vector(item.get("embedding"))
        idx = item.get("index")
        if isinstance(idx, int):
            by_index[idx] = emb
        else:
            positional.append(emb)

    if by_index:
        out = [by_index[i] for i in sorted(by_index.keys())]
    else:
        out = positional

    if expected and len(out) != expected:
        raise EmbeddingError(f"Expected {expected} embeddings, got {len(out)}.")
    return out


def _parse_tei_embed(resp: Any, *, expected: int) -> list[list[float]]:
    # TEI returns either a single vector (list[float]) or list[list[float]].
    if isinstance(resp, list) and resp and all(isinstance(x, (int, float)) for x in resp):
        out = [_as_vector(resp)]
    elif isinstance(resp, list) and all(isinstance(row, list) for row in resp):
        out = [_as_vector(row) for row in resp]
    elif isinstance(resp, dict) and "embeddings" in resp:
        out = _parse_tei_embed(resp.get("embeddings"), expected=expected)
    else:
        raise EmbeddingError("Unsupported embedding response format.")

    if expected and len(out) != expected:
        raise EmbeddingError(f"Expected {expected} embeddings, got {len(out)}.")
    return out


@dataclass(frozen=True)
class EmbeddingClient:
    host: str
    port: int
    model: Optional[str]
    timeout_s: float = 10.0

    @property
    def base_url(self) -> str:
        host = self.host.strip()
        if "://" in host:
            parsed = urlparse(host)
            scheme = parsed.scheme or "http"
            hostname = parsed.hostname or ""
            if not hostname:
                raise EmbeddingError(f"Invalid embedding host URL: {host}")
            port = parsed.port or self.port
            path = (parsed.path or "").rstrip("/")
            base = f"{scheme}://{hostname}:{port}"
            return (base + path).rstrip("/")

        host = host.rstrip("/")
        if host.count(":") == 1 and host.rsplit(":", 1)[1].isdigit():
            return f"http://{host}"
        return f"http://{host}:{self.port}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        items = [str(t) for t in texts]
        if not items:
            return []

        # Try OpenAI-compatible endpoint first when a model is provided.
        if self.model:
            try:
                resp = _post_json(
                    f"{self.base_url}/v1/embeddings",
                    {"model": self.model, "input": items},
                    timeout_s=self.timeout_s,
                )
                return _parse_openai_embeddings(resp, expected=len(items))
            except EmbeddingHTTPError as e:
                if e.status_code not in (404, 405):
                    raise
            except EmbeddingError:
                # Fall back to TEI endpoint.
                pass

        resp2 = _post_json(f"{self.base_url}/embed", {"inputs": items}, timeout_s=self.timeout_s)
        return _parse_tei_embed(resp2, expected=len(items))
