from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .base import Sink
from ..events import UsageEvent


class ConsoleSink(Sink):
    """Sink that prints usage events to stdout (useful for debugging)."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def write(self, event: UsageEvent) -> None:
        if self.verbose:
            # Full JSON output
            d: dict[str, Any] = asdict(event)
            d["ts"] = event.ts.isoformat()
            d["token_breakdown"] = [b.to_dict() for b in event.token_breakdown]
            print(json.dumps(d, indent=2, ensure_ascii=False))
        else:
            # Compact summary
            tokens = event.total_tokens or 0
            cost = f"${event.cost_usd:.6f}" if event.cost_usd else "N/A"
            latency = f"{event.latency_ms}ms" if event.latency_ms else "N/A"

            print(f"[{event.provider}/{event.model}] {tokens} tokens, {cost}, {latency}")
