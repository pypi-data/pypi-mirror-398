from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ValidationStatus = Literal["PASS", "FAIL", "WARN", "ERROR"]
PipelineStatus = Literal["COMPLETE", "ERROR"]
RunStatus = Literal["RUNNING", "COMPLETE"]
RunResult = Literal["PASS", "FAIL", "WARN", "ERROR"]

TENANT_SLUG_REGEX = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class Candidate(BaseModel):
    model_config = ConfigDict(extra="allow")

    cce_id: str | None = None
    title: str | None = None
    content: str = Field(..., min_length=1)
    content_type: Literal["text/markdown"] = "text/markdown"
    source: str | None = None
    labels: dict[str, str] | None = None


class ChunkingOptions(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_chars: int = Field(3500, ge=1)
    overlap_chars: int = Field(250, ge=0)


class ModelsOptions(BaseModel):
    model_config = ConfigDict(extra="allow")

    primary: str | None = None
    fallback: str | None = None


class ValidateOptions(BaseModel):
    model_config = ConfigDict(extra="allow")

    chunking: ChunkingOptions = Field(default_factory=ChunkingOptions)
    models: ModelsOptions = Field(default_factory=ModelsOptions)


class ValidateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_id: str | None = None
    mode: Literal["audit", "smoke", "rectify"] = "audit"
    candidate: Candidate
    options: ValidateOptions = Field(default_factory=ValidateOptions)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str | None = None
    excerpt: str | None = None
    note: str | None = None


class ChunkResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    chunk_id: str
    index: int
    status: ValidationStatus
    model_used: str | None = None
    finding_count: int = 0
    message: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    details: dict[str, Any] | None = None


class ContentSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    pass_: int = Field(0, alias="pass")
    fail: int = 0
    warn: int = 0
    error: int = 0


class Counts(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Accept contract JSON keys (PASS/FAIL/WARN/ERROR) but expose pythonic attributes.
    pass_: int = Field(0, alias="PASS")
    fail: int = Field(0, alias="FAIL")
    warn: int = Field(0, alias="WARN")
    error: int = Field(0, alias="ERROR")
    total_chunks: int = 0


class Links(BaseModel):
    model_config = ConfigDict(extra="allow")

    run: str
    chunks: str


class ValidateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_id: str
    run_id: str
    status: RunStatus
    result: RunResult
    counts: Counts
    links: Links


class RunStateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    tenant_slug: str
    pipeline_status: PipelineStatus
    content_summary: ContentSummary
    inserted_at: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ChunkResultsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    tenant_slug: str
    chunks: list[ChunkResult]


