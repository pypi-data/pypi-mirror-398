from typing import Any, Literal

from pydantic import BaseModel, Field


class PackageReport(BaseModel):
    package: str
    current: str
    status: Literal["update", "skip", "current", "error", "vendor"]
    recommended: str | None = None
    reason: str | None = None
    is_dev: bool = False
    is_major_update: bool = False
    confidence_level: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"] = "UNKNOWN"
    python_min: str | None = None  # Minimum Python version (e.g., 3.8)
    python_max: str | None = None  # Maximum Python version (e.g., 3.13)
    version_jump: Literal["major", "minor", "patch", "unknown"] = "unknown"
    risk_factors: list[str] = Field(default_factory=list)  # List of reasons for risk level
    requires_python: str | None = None  # Package's requires_python from PyPI
    python_constraint: str | None = None  # Calculated constraint to apply

    model_config = {"extra": "forbid"}


class DependencyUpdate(BaseModel):
    package: str
    current_spec: str
    new_spec: str
    is_dev: bool = False
    is_major_update: bool = False

    model_config = {"extra": "forbid"}


class AnalysisResult(BaseModel):
    updates: dict[str, str]  # package > new_version
    skipped: dict[str, str]  # package > reason
    report: list[PackageReport]
    summary: dict[str, int]
    python_version: str | None = None
    original_python: str | None = None  # Original Python version before target override
    major_updates: list[dict[str, Any]] | None = None
    aborted: bool = False
    abort_reason: str | None = None
    current_version_warnings: list[dict[str, str]] | None = (
        None  # Warnings about non-existent current versions
    )
    python_constraints: dict[str, str] | None = None  # package > python constraint

    model_config = {"extra": "forbid"}


class ArgumentConfig(BaseModel):
    file: str | None = None
    update_source_file: bool = False
    json_output: bool = False
    verbose: bool = False
    allow_prerelease: bool = False
    target_python: str | None = None
    ignore_local_deps: bool = False

    model_config = {"extra": "forbid"}
