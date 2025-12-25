import uuid
from typing import Dict, Any, Optional

import httpx

from .models import CheckResult, Decision
from .exceptions import JanusError, JanusConnectionError, JanusAuthError, JanusRateLimitError


class JanusClient:
    """Synchronous Janus SDK client."""

    DEFAULT_BASE_URL = "https://krystalunity.com"
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        tenant_id: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        fail_open: bool = False,
        retry_count: int = 2,
    ):
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.fail_open = fail_open
        self.retry_count = retry_count

        self._client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "X-Tenant-Id": self.tenant_id,
                "X-API-Key": self.api_key,
            },
        )

    def check(self, action: str, params: Dict[str, Any], agent_id: str = "default") -> CheckResult:
        request_id = str(uuid.uuid4())

        for attempt in range(self.retry_count + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/api/sentinel/action/check",
                    json={"agent_id": agent_id, "action": action, "params": params},
                )

                if response.status_code == 401:
                    raise JanusAuthError("Invalid API key")
                if response.status_code == 429:
                    if attempt < self.retry_count:
                        continue
                    raise JanusRateLimitError("Rate limit exceeded")
                if response.status_code >= 400:
                    raise JanusError(f"API error: {response.text}")

                data = response.json()
                return CheckResult(
                    decision=Decision(data["decision"]),
                    reason=data.get("reason", ""),
                    policy_id=data.get("policy_id"),
                    latency_ms=data.get("latency_ms", 0),
                    request_id=request_id,
                )

            except httpx.RequestError as exc:
                if attempt < self.retry_count:
                    continue
                if self.fail_open:
                    return CheckResult(
                        decision=Decision.ALLOW,
                        reason="Fail-open: connection error",
                        policy_id=None,
                        latency_ms=0,
                        request_id=request_id,
                    )
                raise JanusConnectionError(f"Connection failed: {exc}")

        # Should not reach here
        raise JanusError("Unknown error")

    def report(
        self,
        check_result: CheckResult,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        agent_id: str = "default",
        action: Optional[str] = None,
    ) -> None:
        payload = {
            "request_id": check_result.request_id,
            "agent_id": agent_id,
            "action": action or "",
            "status": status,
            "decision": check_result.decision.value,
            "policy_id": check_result.policy_id,
            "result": result,
        }
        try:
            self._client.post(f"{self.base_url}/api/sentinel/action/report", json=payload)
        except Exception:
            # Best-effort; swallow errors
            return

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
