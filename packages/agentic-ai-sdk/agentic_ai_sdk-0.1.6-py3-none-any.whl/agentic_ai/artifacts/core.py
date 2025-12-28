from __future__ import annotations

import json
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from ..ids import generate_short_id


LOGGER = logging.getLogger("agentic_ai.artifacts")


# =============================================================================
# ToolResult - Unified Tool Output Structure
# =============================================================================

class ToolResult(BaseModel):
    """统一的工具输出结构。
    
    字段语义：
    - status: "ok" 表示成功，"error" 表示失败
    - error_message: 仅在 status="error" 时必填
    - result: 返回给 LLM 的数据（可能是预览）
    - artifact_id: 持久化的完整数据引用
    - summary: artifact 元数据（如 row_count, size）
    - is_preview: True 表示 result 是截断预览
    
    Example:
        # 成功响应
        ToolResult(result={"data": "value"})
        ToolResult(result=preview_data, artifact_id="abc123", is_preview=True)
        
        # 错误响应
        ToolResult(status="error", error_message="Failed to execute", result={"error": "..."})
    """
    status: Literal["ok", "error"] = "ok"
    error_message: str | None = None
    result: Any | None = None
    artifact_id: str | None = None
    summary: dict[str, Any] | None = None
    is_preview: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate(self) -> "ToolResult":
        if self.status == "error" and not self.error_message:
            raise ValueError("error_message required when status=error")
        if self.status == "ok" and self.result is None and self.artifact_id is None:
            raise ValueError("result or artifact_id required when status=ok")
        return self

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """序列化时默认排除 None 值以减少 token 消耗。"""
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class ArtifactStore:
    """Utility responsible for writing tool artifacts into the workspace."""

    def __init__(self, workspace_dir: Path):
        self._workspace_dir = workspace_dir
        self._workspace_dir.mkdir(parents=True, exist_ok=True)

    @property
    def workspace_dir(self) -> Path:
        return self._workspace_dir

    def artifact_path(self, artifact_id: str) -> Path:
        return self._workspace_dir / artifact_id

    def create_artifact_dir(self, artifact_id: Optional[str] = None) -> tuple[str, Path]:
        resolved_id = artifact_id or generate_short_id()
        path = self.artifact_path(resolved_id)
        path.mkdir(parents=True, exist_ok=False)
        return resolved_id, path

    def write_manifest(self, artifact_id: str, manifest: dict[str, Any]) -> Path:
        target_dir = self.artifact_path(artifact_id)
        if not target_dir.exists():
            raise FileNotFoundError(f"Artifact directory missing for id '{artifact_id}'.")
        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, default=str))
        return manifest_path

    def create_json_artifact(
        self,
        data: Any,
        *,
        artifact_id: str | None = None,
        filename: str = "data.json",
        media_type: str = "application/json",
        manifest_type: str = "dataset",
        manifest_overrides: dict[str, Any] | None = None,
    ) -> tuple[str, Path]:
        """Persist JSON-serializable data and return the artifact identifier."""
        resolved_id, directory = self.create_artifact_dir(artifact_id)
        data_path = directory / filename
        data_path.write_text(json.dumps(data, ensure_ascii=False, default=str))
        manifest = {
            "type": manifest_type,
            "files": [{"path": filename, "media_type": media_type}],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if manifest_overrides:
            manifest.update(manifest_overrides)
        self.write_manifest(resolved_id, manifest)
        return resolved_id, directory


# =============================================================================
# Helper Functions - Simplified persist/ok/error API
# =============================================================================

def _get_artifact_store() -> ArtifactStore:
    """Get artifact store from current context."""
    from ..runtime.contexts import ctx
    context = ctx()
    if context.artifact_store is None:
        raise RuntimeError("No artifact store available in current context.")
    return context.artifact_store


def persist_full(
    data: Any,
    *,
    summary: dict[str, Any] | None = None,
    filename: str = "data.json",
    manifest_overrides: dict[str, Any] | None = None,
    store: ArtifactStore | None = None,
) -> ToolResult:
    """持久化完整数据，result 返回全量数据。
    
    适用场景：数据量小，无需截断。
    
    Args:
        data: 要持久化的数据
        summary: artifact 元数据
        filename: 文件名
        manifest_overrides: manifest 覆盖项
        store: 显式指定 ArtifactStore（可选）
        
    Returns:
        ToolResult with result=data and artifact_id
    """
    if store is None:
        store = _get_artifact_store()
    
    artifact_id, _ = store.create_json_artifact(
        data=data,
        filename=filename,
        manifest_overrides=manifest_overrides,
    )
    return ToolResult(
        result=data,
        artifact_id=artifact_id,
        summary=summary,
        is_preview=False,
    )


def persist_preview(
    full_data: Any,
    *,
    preview_rows: int | None = None,
    summary: dict[str, Any] | None = None,
    filename: str = "data.json",
    manifest_overrides: dict[str, Any] | None = None,
    store: ArtifactStore | None = None,
) -> ToolResult:
    """持久化完整数据，result 返回截断预览。
    
    适用场景：数据量大，需要截断以节省 token。
    自动处理 {"rows": [...]} 结构的截断。
    
    Args:
        full_data: 完整数据（将被持久化）
        preview_rows: 预览行数（默认从 tools.yaml 配置读取，若无配置则为 200）
        summary: artifact 元数据
        filename: 文件名
        manifest_overrides: manifest 覆盖项
        store: 显式指定 ArtifactStore（可选）
        
    Returns:
        ToolResult with preview result and artifact_id
    """
    if store is None:
        store = _get_artifact_store()
    
    # 自动从配置读取 preview_rows
    if preview_rows is None:
        from ..runtime.tool_runtime import get_output_config
        output_config = get_output_config()
        preview_rows = output_config.get("preview_rows", 200)
    
    # Ensure preview_rows is an int (type guard)
    effective_preview_rows: int = preview_rows if preview_rows is not None else 200
    
    artifact_id, _ = store.create_json_artifact(
        data=full_data,
        filename=filename,
        manifest_overrides=manifest_overrides,
    )
    
    # 自动截断 rows
    if isinstance(full_data, dict) and "rows" in full_data:
        rows = full_data["rows"]
        if isinstance(rows, list) and len(rows) > effective_preview_rows:
            preview_data = {**full_data, "rows": rows[:effective_preview_rows]}
            return ToolResult(
                result=preview_data,
                artifact_id=artifact_id,
                summary=summary,
                is_preview=True,
            )
    
    return ToolResult(
        result=full_data,
        artifact_id=artifact_id,
        summary=summary,
        is_preview=False,
    )


def ok(
    result: Any,
    *,
    artifact_id: str | None = None,
    summary: dict[str, Any] | None = None,
) -> ToolResult:
    """快速构造成功响应。
    
    Args:
        result: 返回结果
        artifact_id: 可选 artifact 引用
        summary: 可选摘要信息
        
    Returns:
        ToolResult with status="ok"
    """
    return ToolResult(result=result, artifact_id=artifact_id, summary=summary)


def error(message: str, *, result: Any | None = None) -> ToolResult:
    """快速构造错误响应。
    
    Args:
        message: 错误消息
        result: 可选附加信息
        
    Returns:
        ToolResult with status="error"
    """
    return ToolResult(
        status="error",
        error_message=message,
        result=result if result is not None else {"error": message},
    )


# =============================================================================
# Artifact Loading - Explicit Failure
# =============================================================================


def _get_workspace_dir(workspace_dir: Path | str | None = None) -> Path:
    """Get workspace directory from parameter or context."""
    if workspace_dir is not None:
        return Path(workspace_dir)
    
    from ..runtime.contexts import try_ctx
    context = try_ctx()
    if context is None or context.artifact_store is None:
        raise RuntimeError(
            "No tool context available. Provide workspace_dir explicitly or "
            "ensure tool is invoked via SDK middleware."
        )
    return context.artifact_store.workspace_dir


def load_artifact(
    artifact_id: str,
    *,
    filename: str = "data.json",
    format: Literal["json", "text", "binary"] = "json",
    workspace_dir: Path | str | None = None,
) -> Any:
    """从 artifact 加载数据（显式失败）。
    
    Args:
        artifact_id: artifact 标识符
        filename: 文件名
        format: 格式（json/text/binary）
        workspace_dir: 显式指定工作目录（可选，默认从上下文获取）
        
    Returns:
        加载的数据
        
    Raises:
        ValueError: artifact_id 为空
        RuntimeError: 无可用上下文且未提供 workspace_dir
        FileNotFoundError: artifact 不存在
    """
    if not artifact_id:
        raise ValueError("artifact_id is required")
    
    base = _get_workspace_dir(workspace_dir)
    path = base / artifact_id / filename
    
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_id}/{filename}")

    if format == "json":
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in artifact {artifact_id}/{filename}: {exc}") from exc
    if format == "text":
        return path.read_text()
    return path.read_bytes()


def try_load_artifact(
    artifact_id: str,
    *,
    default: Any = None,
    **kwargs,
) -> Any:
    """尝试加载 artifact，失败时返回默认值。
    
    与 load_artifact 不同，此函数不会抛异常。
    适用于：已知 artifact 可能不存在的场景。
    """
    if not artifact_id:
        return default
    try:
        return load_artifact(artifact_id, **kwargs)
    except (ValueError, RuntimeError, FileNotFoundError):
        return default


__all__ = [
    # Core types
    "ArtifactStore",
    "ToolResult",
    # Helpers
    "persist_full",
    "persist_preview",
    "ok",
    "error",
    "load_artifact",
    "try_load_artifact",
]
