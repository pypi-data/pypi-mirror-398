from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, SecretStr

from vibemem.models import PrincipalType
from vibemem.store.base import ConfigError


CacheMode = Literal["auto", "on", "off"]


class VibememConfig(BaseModel):
    weaviate_url: Optional[str] = Field(default=None)
    weaviate_grpc_url: Optional[str] = Field(default=None)
    weaviate_api_key: Optional[SecretStr] = Field(default=None)

    # Optional client-side embeddings (for Weaviate classes with vectorizer = none).
    embedding_host: Optional[str] = Field(default=None)
    embedding_port: Optional[int] = Field(default=None, ge=1, le=65535)
    embedding_model: Optional[str] = Field(default=None)

    weaviate_collection: str = Field(default="VibeMemMemory")
    cache_mode: CacheMode = Field(default="auto")

    # Optional defaults for ownership / audience fields when creating memories.
    principal_type: Optional[PrincipalType] = Field(default=None)
    principal_id: Optional[str] = Field(default=None)

    request_timeout_s: float = Field(default=10.0, ge=1.0, le=120.0)

    @staticmethod
    def config_dir() -> Path:
        path = Path.home() / ".vibemem"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def config_file() -> Path:
        return VibememConfig.config_dir() / "config"


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"Invalid JSON in config file {path} (line {e.lineno} column {e.colno}): {e.msg}"
        ) from e
    except OSError as e:
        raise ConfigError(f"Failed to read config file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError(f"Config file {path} must contain a JSON object at the top level.")
    return data


def read_config_file(*, path: Optional[Path] = None) -> dict:
    return _read_json_file(path or VibememConfig.config_file())


def write_config_file(data: dict, *, path: Optional[Path] = None) -> Path:
    out_path = path or VibememConfig.config_file()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = out_path.with_name(out_path.name + ".tmp")
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"

    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, out_path)
    except OSError as e:
        raise ConfigError(f"Failed to write config file {out_path}: {e}") from e
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass

    if os.name != "nt":
        try:
            os.chmod(out_path, 0o600)
        except OSError:
            pass

    return out_path


def load_config() -> VibememConfig:
    file_data = _read_json_file(VibememConfig.config_file())

    env_data: dict = {}
    if os.getenv("VIBEMEM_WEAVIATE_URL"):
        env_data["weaviate_url"] = os.getenv("VIBEMEM_WEAVIATE_URL")
    if os.getenv("VIBEMEM_WEAVIATE_GRPC_URL"):
        env_data["weaviate_grpc_url"] = os.getenv("VIBEMEM_WEAVIATE_GRPC_URL")
    if os.getenv("VIBEMEM_WEAVIATE_API_KEY"):
        env_data["weaviate_api_key"] = os.getenv("VIBEMEM_WEAVIATE_API_KEY")
    if os.getenv("VIBEMEM_WEAVIATE_COLLECTION"):
        env_data["weaviate_collection"] = os.getenv("VIBEMEM_WEAVIATE_COLLECTION")
    if os.getenv("VIBEMEM_CACHE_MODE"):
        env_data["cache_mode"] = os.getenv("VIBEMEM_CACHE_MODE")
    if os.getenv("VIBEMEM_PRINCIPAL_TYPE"):
        env_data["principal_type"] = os.getenv("VIBEMEM_PRINCIPAL_TYPE")
    if os.getenv("VIBEMEM_PRINCIPAL_ID"):
        env_data["principal_id"] = os.getenv("VIBEMEM_PRINCIPAL_ID")

    if os.getenv("VIBEMEM_EMBEDDING_HOST"):
        env_data["embedding_host"] = os.getenv("VIBEMEM_EMBEDDING_HOST")
    if os.getenv("VIBEMEM_EMBEDDING_PORT"):
        env_data["embedding_port"] = os.getenv("VIBEMEM_EMBEDDING_PORT")
    if os.getenv("VIBEMEM_EMBEDDING_MODEL"):
        env_data["embedding_model"] = os.getenv("VIBEMEM_EMBEDDING_MODEL")

    merged = dict(file_data)
    merged.update(env_data)
    return VibememConfig.model_validate(merged)


def redact_config_for_display(cfg: VibememConfig) -> dict:
    return {
        "weaviate_url": cfg.weaviate_url,
        "weaviate_grpc_url": cfg.weaviate_grpc_url,
        "weaviate_api_key": "***redacted***" if cfg.weaviate_api_key else None,
        "embedding_host": cfg.embedding_host,
        "embedding_port": cfg.embedding_port,
        "embedding_model": cfg.embedding_model,
        "weaviate_collection": cfg.weaviate_collection,
        "cache_mode": cfg.cache_mode,
        "principal_type": cfg.principal_type.value if cfg.principal_type else None,
        "principal_id": cfg.principal_id,
        "request_timeout_s": cfg.request_timeout_s,
        "config_file": str(cfg.config_file()),
    }
