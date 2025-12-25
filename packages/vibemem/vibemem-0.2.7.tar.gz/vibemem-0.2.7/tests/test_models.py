from __future__ import annotations

import pytest
from pydantic import ValidationError

from vibemem.models import Confidence, MemType, Memory, MemoryUpdate, ScopeType, memory_to_weaviate_properties


def test_memory_validation_requires_text() -> None:
    with pytest.raises(ValidationError):
        Memory(
            text="",
            mem_type=MemType.finding,
            tags=[],
            scope_type=ScopeType.project,
            scope_id="repo",
            repo="repo",
            rel_path="",
        )


def test_memory_dedupes_tags() -> None:
    m = Memory(
        text="hello",
        mem_type=MemType.finding,
        tags=["a", "a", " b ", ""],
        scope_type=ScopeType.project,
        scope_id="repo",
        repo="repo",
        rel_path="",
    )
    assert m.tags == ["a", "b"]


def test_memory_update_strips_text() -> None:
    u = MemoryUpdate(text="  hi  ")
    assert u.text == "hi"


def test_memory_to_weaviate_properties_omits_none_fields() -> None:
    m = Memory(
        text="hello",
        mem_type=MemType.finding,
        tags=[],
        scope_type=ScopeType.project,
        scope_id="repo",
        repo="repo",
        rel_path="",
        confidence=Confidence.med,
        verification=None,
        error_signatures=None,
        files=None,
        commands_run=None,
    )
    props = memory_to_weaviate_properties(m)
    assert "verification" not in props
    assert "error_signatures" not in props
    assert "files" not in props
    assert "commands_run" not in props