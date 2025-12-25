from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class Decision(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


@dataclass
class CheckResult:
    decision: Decision
    reason: str
    policy_id: Optional[str]
    latency_ms: int
    request_id: str

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    @property
    def denied(self) -> bool:
        return self.decision == Decision.DENY

    @property
    def requires_approval(self) -> bool:
        return self.decision == Decision.APPROVAL_REQUIRED


@dataclass
class CheckRequest:
    agent_id: str
    action: str
    params: Dict[str, Any]


@dataclass
class ReportRequest:
    request_id: str
    agent_id: str
    action: str
    status: str  # success, failure, error
    result: Optional[Dict[str, Any]] = None
