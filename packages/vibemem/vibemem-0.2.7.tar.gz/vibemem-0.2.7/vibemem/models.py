from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import getpass
import os
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_dt() -> datetime:
    return datetime.now(tz=timezone.utc).replace(microsecond=0)


def _now_iso() -> str:
    return _now_dt().isoformat()

def _default_principal_id() -> str:
    v = (os.getenv("VIBEMEM_PRINCIPAL_ID") or "").strip()
    if v:
        return v
    try:
        v = (getpass.getuser() or "").strip()
    except Exception:
        v = ""
    return v or "unknown"


class MemType(str, Enum):
    core = "core"
    finding = "finding"
    recipe = "recipe"
    gotcha = "gotcha"
    preference = "preference"


class ScopeType(str, Enum):
    global_ = "global"
    project = "project"


class Confidence(str, Enum):
    low = "low"
    med = "med"
    high = "high"

class PrincipalType(str, Enum):
    user = "user"
    bot = "bot"
    org = "org"
    shared = "shared"


class Memory(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid4()))

    text: str = Field(min_length=1)
    mem_type: MemType
    tags: list[str] = Field(default_factory=list)

    principal_type: PrincipalType = Field(default=PrincipalType.user)
    principal_id: str = Field(default_factory=_default_principal_id, min_length=1)
    bot_id: Optional[str] = Field(default=None)

    scope_type: ScopeType
    scope_id: str = Field(min_length=1)
    repo: str = Field(default="")
    rel_path: str = Field(default="")

    confidence: Confidence = Field(default=Confidence.med)
    verification: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=_now_dt)
    updated_at: datetime = Field(default_factory=_now_dt)

    error_signatures: Optional[list[str]] = Field(default=None)
    files: Optional[list[str]] = Field(default=None)
    commands_run: Optional[list[str]] = Field(default=None)

    @field_validator("tags")
    @classmethod
    def _dedupe_tags(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for t in v:
            t2 = t.strip()
            if not t2:
                continue
            if t2 in seen:
                continue
            cleaned.append(t2)
            seen.add(t2)
        return cleaned

    @field_validator("rel_path")
    @classmethod
    def _normalize_rel_path(cls, v: str) -> str:
        v = (v or "").strip()
        if v in (".", "./"):
            return ""
        return v.replace("\\", "/")

    @field_validator("principal_id")
    @classmethod
    def _strip_principal_id(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("principal_id must be non-empty")
        return v

    @field_validator("bot_id")
    @classmethod
    def _normalize_bot_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("text")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must be non-empty")
        return v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _blank_dt_to_now(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return _now_dt()
        return v

    @field_validator("created_at", "updated_at")
    @classmethod
    def _normalize_dt(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc)
        return v.replace(microsecond=0)


class MemoryUpdate(BaseModel):
    text: Optional[str] = None
    mem_type: Optional[MemType] = None
    tags: Optional[list[str]] = None
    principal_type: Optional[PrincipalType] = None
    principal_id: Optional[str] = None
    bot_id: Optional[str] = None
    confidence: Optional[Confidence] = None
    verification: Optional[str] = None

    @field_validator("text")
    @classmethod
    def _strip_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("text must be non-empty")
        return v

    @field_validator("principal_id")
    @classmethod
    def _strip_principal_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("principal_id must be non-empty")
        return v


class SearchHit(BaseModel):
    id: str
    score: float
    memory: Memory
    source: str = Field(default="weaviate")  # "weaviate" | "chroma" | "merged"


class ListFilters(BaseModel):
    scope: str = Field(default="project")  # "global" | "project" | "all"
    mem_type: Optional[MemType] = None
    tag: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=200)

    # Optional partitioning helpers (used by CLI for repo-local listing and sync).
    repo: Optional[str] = None
    scope_ids: Optional[list[str]] = None


def memory_to_weaviate_properties(memory: Memory) -> dict[str, Any]:
    props: dict[str, Any] = {
        "text": memory.text,
        "mem_type": memory.mem_type.value,
        "tags": memory.tags,
        "principal_type": memory.principal_type.value,
        "principal_id": memory.principal_id,
        "bot_id": memory.bot_id,
        "scope_type": memory.scope_type.value,
        "scope_id": memory.scope_id,
        "repo": memory.repo,
        "rel_path": memory.rel_path,
        "confidence": memory.confidence.value,
        "verification": memory.verification,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "error_signatures": memory.error_signatures,
        "files": memory.files,
        "commands_run": memory.commands_run,
    }
    return {k: v for k, v in props.items() if v is not None}


def memory_from_properties(id: str, props: dict[str, Any]) -> Memory:
    return Memory.model_validate(
        {
            "id": id,
            **props,
        }
    )
