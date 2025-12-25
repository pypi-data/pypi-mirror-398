from functools import wraps
from typing import Callable, Any, Dict

from .client import JanusClient
from .async_client import AsyncJanusClient
from .exceptions import JanusError


def janus_guard(client: JanusClient, action: str, agent_id: str = "default", param_extractor: Callable[..., Dict[str, Any]] = None):
    """
    Decorator to wrap a synchronous function with Janus checks.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            params = param_extractor(*args, **kwargs) if param_extractor else kwargs
            result = client.check(action=action, params=params, agent_id=agent_id)

            if result.denied:
                raise PermissionError(f"Action denied: {result.reason}")
            if result.requires_approval:
                raise PermissionError(f"Action requires approval: {result.reason}")

            try:
                outcome = func(*args, **kwargs)
                client.report(result, status="success", result=None, agent_id=agent_id, action=action)
                return outcome
            except Exception as exc:
                client.report(result, status="error", result={"error": str(exc)}, agent_id=agent_id, action=action)
                raise

        return wrapper

    return decorator


def ajanus_guard(client: AsyncJanusClient, action: str, agent_id: str = "default", param_extractor: Callable[..., Dict[str, Any]] = None):
    """Async decorator version."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            params = param_extractor(*args, **kwargs) if param_extractor else kwargs
            result = await client.check(action=action, params=params, agent_id=agent_id)

            if result.denied:
                raise PermissionError(f"Action denied: {result.reason}")
            if result.requires_approval:
                raise PermissionError(f"Action requires approval: {result.reason}")

            try:
                outcome = await func(*args, **kwargs)
                await client.report(result, status="success", result=None, agent_id=agent_id, action=action)
                return outcome
            except Exception as exc:
                await client.report(result, status="error", result={"error": str(exc)}, agent_id=agent_id, action=action)
                raise

        return wrapper

    return decorator


def openai_guard(client: JanusClient, agent_id: str = "openai-agent"):
    """
    Decorator for OpenAI calls (sync). Action inferred from function name.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            action = f"llm.{func.__name__}"
            params = {"kwargs_keys": list(kwargs.keys())}
            result = client.check(action=action, params=params, agent_id=agent_id)
            if not result.allowed:
                raise PermissionError(f"LLM call blocked: {result.reason}")
            try:
                outcome = func(*args, **kwargs)
                client.report(result, status="success", result=None, agent_id=agent_id, action=action)
                return outcome
            except Exception as exc:
                client.report(result, status="error", result={"error": str(exc)}, agent_id=agent_id, action=action)
                raise

        return wrapper

    return decorator
