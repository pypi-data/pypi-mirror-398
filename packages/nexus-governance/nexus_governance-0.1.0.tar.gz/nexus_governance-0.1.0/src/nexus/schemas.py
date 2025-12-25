from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Danger(str, Enum):
    READ_ONLY = "read"
    WRITE = "write"
    CRITICAL = "critical"


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    THROTTLE = "throttle"


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    role: str = "viewer"
    tenant_id: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class AuditRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(default_factory=utcnow)
    trace_id: str
    principal: Principal
    tool_name: str
    tool_version: str
    danger: Danger
    verdict: Verdict
    reason: Optional[str] = None
    execution_hash: str
