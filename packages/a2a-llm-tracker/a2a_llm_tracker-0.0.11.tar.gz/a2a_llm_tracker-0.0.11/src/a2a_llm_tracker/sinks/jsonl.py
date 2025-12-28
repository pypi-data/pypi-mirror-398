from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .base import Sink
from ..events import UsageEvent


class JSONLSink(Sink):
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: UsageEvent) -> None:
        d: dict[str, Any] = asdict(event)
        # datetime -> iso
        d["ts"] = event.ts.isoformat()
        # Convert token breakdown to list of dicts
        d["token_breakdown"] = [b.to_dict() for b in event.token_breakdown]
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
