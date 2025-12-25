from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Optional, Sequence

from pydantic import BaseModel
from rich.console import Console
from rich.pretty import Pretty


_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def parse_csv_list(s: Optional[str]) -> list[str]:
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def uniq(seq: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for x in seq:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def normalize_where_paths(paths: Sequence[str]) -> list[str]:
    return [p.replace("\\", "/").strip() for p in paths if p.strip()]


def _to_primitive(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_primitive(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_primitive(v) for v in obj]
    if isinstance(obj, BaseModel):
        return _to_primitive(obj.model_dump(mode="json"))
    if is_dataclass(obj) and not isinstance(obj, type):
        return _to_primitive(asdict(obj))
    return str(obj)


def emit(obj: Any, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_to_primitive(obj), indent=None, separators=(",", ":"), sort_keys=False))
        return

    console = Console()
    console.print(Pretty(_to_primitive(obj), max_depth=6))


def simple_text_score(query: str, text: str) -> float:
    q_words = set(w.lower() for w in _WORD_RE.findall(query))
    t_words = set(w.lower() for w in _WORD_RE.findall(text))
    if not q_words or not t_words:
        return 0.0
    inter = len(q_words & t_words)
    return inter / float(len(q_words))


def dedupe_hits_by_id(hits: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for h in hits:
        hid = str(h.get("id", ""))
        if not hid or hid in seen:
            continue
        seen.add(hid)
        out.append(h)
    return out