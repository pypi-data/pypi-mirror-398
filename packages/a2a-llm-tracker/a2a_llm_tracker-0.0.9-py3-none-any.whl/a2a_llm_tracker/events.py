from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, List, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TokenBreakdown:
    """
    Breakdown of token usage by modality type.

    Types: "text", "image", "audio", "video"
    """
    type: str  # "text", "image", "audio", "video"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    count: Optional[int] = None  # Number of items (e.g., images, audio clips)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UsageEvent:
    provider: str
    model: str

    # Token breakdown by modality type
    token_breakdown: List[TokenBreakdown] = field(default_factory=list)

    input_cost_usd: Optional[float] = None
    output_cost_usd: Optional[float] = None
    cost_usd: Optional[float] = None

    accuracy: str = "unknown"  # "exact" | "estimated" | "unknown"

    request_id: Optional[str] = None
    latency_ms: Optional[int] = None
    status: str = "ok"  # "ok" | "error"
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    ts: datetime = field(default_factory=utcnow)

    # attribution
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_input_tokens(self) -> Optional[int]:
        """Sum of all input tokens across all modalities."""
        tokens = [b.input_tokens for b in self.token_breakdown if b.input_tokens is not None]
        return sum(tokens) if tokens else None

    @property
    def total_output_tokens(self) -> Optional[int]:
        """Sum of all output tokens across all modalities."""
        tokens = [b.output_tokens for b in self.token_breakdown if b.output_tokens is not None]
        return sum(tokens) if tokens else None

    @property
    def total_tokens(self) -> Optional[int]:
        """Sum of all tokens (input + output) across all modalities."""
        inp = self.total_input_tokens
        out = self.total_output_tokens
        if inp is None and out is None:
            return None
        return (inp or 0) + (out or 0)

    def get_breakdown(self, type: str) -> Optional[TokenBreakdown]:
        """Get breakdown for a specific type (text, image, audio, video)."""
        for b in self.token_breakdown:
            if b.type == type:
                return b
        return None
