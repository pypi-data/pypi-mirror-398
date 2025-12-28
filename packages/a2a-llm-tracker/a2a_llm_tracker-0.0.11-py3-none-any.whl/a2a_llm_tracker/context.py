from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass(frozen=True)
class MeterContext:
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None


_CTX: ContextVar[MeterContext] = ContextVar("agent_meter_context", default=MeterContext())


def get_context() -> MeterContext:
    return _CTX.get()


def set_context(
    *,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    current = _CTX.get()
    _CTX.set(
        MeterContext(
            agent_id=agent_id if agent_id is not None else current.agent_id,
            user_id=user_id if user_id is not None else current.user_id,
            session_id=session_id if session_id is not None else current.session_id,
            trace_id=trace_id if trace_id is not None else current.trace_id,
        )
    )


@contextmanager
def meter_context(
    *,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Iterator[None]:
    token = _CTX.set(
        MeterContext(agent_id=agent_id, user_id=user_id, session_id=session_id, trace_id=trace_id)
    )
    try:
        yield
    finally:
        _CTX.reset(token)
