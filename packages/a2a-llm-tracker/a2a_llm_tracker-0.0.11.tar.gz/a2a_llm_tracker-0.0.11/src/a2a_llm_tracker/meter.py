from __future__ import annotations

from typing import Iterable, Optional

from .context import get_context
from .events import UsageEvent
from .pricing import ModelPrice, PricingRegistry
from .sinks.base import Sink


class Meter:
    def __init__(
        self,
        *,
        pricing: Optional[PricingRegistry] = None,
        sinks: Optional[Iterable[Sink]] = None,
        project: Optional[str] = None,
    ) -> None:
        self.pricing = pricing or PricingRegistry()
        self.sinks = list(sinks or [])
        self.project = project

    def compute_cost(
        self,
        provider: str,
        model: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[ModelPrice]]:
        price = self.pricing.get_price(provider, model)
        if price is None or input_tokens is None or output_tokens is None:
            return None, None, None, price

        in_cost = (input_tokens / 1_000_000) * price.input_per_million
        out_cost = (output_tokens / 1_000_000) * price.output_per_million
        return in_cost, out_cost, (in_cost + out_cost), price

    def record(self, event: UsageEvent) -> None:
        # enrich with context if missing
        ctx = get_context()
        event.agent_id = event.agent_id or ctx.agent_id
        event.user_id = event.user_id or ctx.user_id
        event.session_id = event.session_id or ctx.session_id
        event.trace_id = event.trace_id or ctx.trace_id

        if self.project:
            event.metadata.setdefault("project", self.project)

        for sink in self.sinks:
            sink.write(event)
