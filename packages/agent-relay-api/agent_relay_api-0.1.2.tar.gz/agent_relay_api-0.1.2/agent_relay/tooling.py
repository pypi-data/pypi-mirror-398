# tooling.py
from __future__ import annotations
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional, Protocol

from .context import get_current_session

ToolCall = Callable[..., Any]


class RuntimeLike(Protocol):
    compensations: Dict[str, str]

    def register_tool(self, name: str, func: ToolCall) -> None: ...
    def register_compensation(self, tool_name: str, compensation_tool_name: str) -> None: ...


def tool(
    runtime: RuntimeLike,
    name: Optional[str] = None,
    compensation: Optional[str] = None,
) -> Callable[[ToolCall], ToolCall]:
    """
    Decorator for tools.

    - Inside an active session: logs usage/traces by routing through session.execute_tool_call(...)
    - Outside a session: calls function directly, unless AGENTTRAIL_ENFORCE_SESSION=1
    """
    enforce = os.environ.get("AGENTTRAIL_ENFORCE_SESSION", "0") == "1"

    def decorator(func: ToolCall) -> ToolCall:
        tool_name = name or func.__name__

        runtime.register_tool(tool_name, func)
        if compensation:
            runtime.register_compensation(tool_name, compensation)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = get_current_session()

            if session is None:
                if enforce:
                    raise RuntimeError(
                        f'Tool "{tool_name}" was called without an active session and AGENTTRAIL_ENFORCE_SESSION=1'
                    )
                return func(*args, **kwargs)

            if hasattr(session, "runtime") and session.runtime is not runtime:
                raise RuntimeError(
                    f'Tool "{tool_name}" was registered on a different runtime instance than the active session.'
                )

            compensation_name = (
                runtime.compensations.get(tool_name)
                if not getattr(session, "replay", False)
                else None
            )

            return session.execute_tool_call(
                tool_name=tool_name,
                func=func,
                args=args,
                kwargs=kwargs,
                phase="forward",
                compensation_tool_name=compensation_name,
            )

        return wrapper  # type: ignore[return-value]

    return decorator
