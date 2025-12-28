from __future__ import annotations

import time
from typing import Any, AsyncIterator, Iterator, List, Optional, Tuple

from ..events import TokenBreakdown, UsageEvent
from ..images import analyze_audio_in_messages, analyze_images_in_messages
from ..meter import Meter


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    # works for dicts and objects
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _extract_usage(resp_or_chunk: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    LiteLLM often returns a response with:
      - resp.usage.prompt_tokens / completion_tokens / total_tokens
    For streaming, some configs return usage in the final chunk.
    """
    usage = _get_attr(resp_or_chunk, "usage", None)
    if usage is None:
        # sometimes nested differently; keep this minimal for v1
        return None, None, None

    in_tok = _get_attr(usage, "prompt_tokens", None)
    out_tok = _get_attr(usage, "completion_tokens", None)
    total = _get_attr(usage, "total_tokens", None)

    # Sometimes LiteLLM usage might be dict-like
    if isinstance(usage, dict):
        in_tok = usage.get("prompt_tokens", in_tok)
        out_tok = usage.get("completion_tokens", out_tok)
        total = usage.get("total_tokens", total)

    return in_tok, out_tok, total


def _guess_provider_from_model(model: str) -> str:
    """
    LiteLLM supports prefixes like 'openai/gpt-4o-mini', 'anthropic/claude-...'.
    If absent, we default to 'litellm'.
    """
    if "/" in model:
        return model.split("/", 1)[0].lower()
    if ":" in model:
        return model.split(":", 1)[0].lower()
    return "litellm"


def _build_token_breakdown(
    in_tok: Optional[int],
    out_tok: Optional[int],
    image_breakdown: Optional[TokenBreakdown],
    audio_breakdown: Optional[TokenBreakdown] = None,
) -> List[TokenBreakdown]:
    """Build token breakdown list from text tokens and media breakdowns."""
    breakdown: List[TokenBreakdown] = []

    # Add text tokens (provider-reported, exact)
    if in_tok is not None or out_tok is not None:
        breakdown.append(TokenBreakdown(
            type="text",
            input_tokens=in_tok,
            output_tokens=out_tok,
        ))

    # Add image tokens (estimated)
    if image_breakdown is not None:
        breakdown.append(image_breakdown)

    # Add audio tokens (estimated)
    if audio_breakdown is not None:
        breakdown.append(audio_breakdown)

    return breakdown


class _StreamWrapper(Iterator[Any]):
    def __init__(self, inner: Iterator[Any], finalize) -> None:
        self._inner = inner
        self._finalize = finalize
        self._done = False

    def __iter__(self) -> "_StreamWrapper":
        return self

    def __next__(self) -> Any:
        try:
            return next(self._inner)
        except StopIteration:
            if not self._done:
                self._done = True
                self._finalize()
            raise
        except Exception:
            if not self._done:
                self._done = True
                self._finalize(error=True)
            raise


class _AsyncStreamWrapper(AsyncIterator[Any]):
    def __init__(self, inner: AsyncIterator[Any], finalize) -> None:
        self._inner = inner
        self._finalize = finalize
        self._done = False

    def __aiter__(self) -> "_AsyncStreamWrapper":
        return self

    async def __anext__(self) -> Any:
        try:
            return await self._inner.__anext__()
        except StopAsyncIteration:
            if not self._done:
                self._done = True
                self._finalize()
            raise
        except Exception:
            if not self._done:
                self._done = True
                self._finalize(error=True)
            raise


class LiteLLM:
    """
    LiteLLM-first wrapper.
    - completion(): sync
    - acompletion(): async
    Supports stream=True and stream=False.
    """

    def __init__(self, *, meter: Optional[Meter] = None) -> None:
        if meter is None:
            # Use global meter from init()
            from ..config import get_meter
            meter = get_meter()

        self.meter = meter

        try:
            import litellm  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "litellm is not installed. Install with: pip install -e '.[litellm]'"
            ) from e

        self._litellm = litellm

    def completion(self, **kwargs: Any):
        """
        Mirrors litellm.completion(**kwargs).
        If stream=True, returns an iterator you can for-loop; event is recorded when stream ends.
        """
        model = kwargs.get("model", "unknown")
        provider = _guess_provider_from_model(model)

        stream = bool(kwargs.get("stream", False))

        # Analyze media in messages
        messages = kwargs.get("messages", [])
        image_breakdown = analyze_images_in_messages(messages, provider)
        audio_breakdown = analyze_audio_in_messages(messages, provider)

        # Best effort: ask for usage in streaming if supported by downstream.
        # Not all providers respect this; we still handle missing usage.
        kwargs.setdefault("stream_options", {"include_usage": True})

        t0 = time.time()
        last_chunk_holder: dict[str, Any] = {"last": None}
        status = "ok"
        err_type = None
        err_msg = None
        request_id: Optional[str] = None
        final_model: str = model

        def finalize(error: bool = False) -> None:
            latency_ms = int((time.time() - t0) * 1000)

            resp_or_chunk = last_chunk_holder["last"]
            in_tok = out_tok = total = None

            if resp_or_chunk is not None:
                in_tok, out_tok, total = _extract_usage(resp_or_chunk)
                request_id_local = _get_attr(resp_or_chunk, "id", None)
                nonlocal request_id, final_model
                if request_id is None:
                    request_id = request_id_local
                final_model = _get_attr(resp_or_chunk, "model", final_model) or final_model

            accuracy = "exact" if (in_tok is not None and out_tok is not None) else "unknown"
            in_cost, out_cost, cost, _price = self.meter.compute_cost(provider, final_model, in_tok, out_tok)
            token_breakdown = _build_token_breakdown(in_tok, out_tok, image_breakdown, audio_breakdown)

            event = UsageEvent(
                provider=provider,
                model=final_model,
                token_breakdown=token_breakdown,
                input_cost_usd=in_cost,
                output_cost_usd=out_cost,
                cost_usd=cost,
                accuracy=accuracy,
                request_id=request_id,
                latency_ms=latency_ms,
                status="error" if error else status,
                error_type=err_type,
                error_message=err_msg,
                metadata={"integration": "litellm", "stream": stream},
            )
            self.meter.record(event)

        try:
            resp = self._litellm.completion(**kwargs)
            if not stream:
                latency_ms = int((time.time() - t0) * 1000)

                request_id = _get_attr(resp, "id", None)
                final_model = _get_attr(resp, "model", model) or model
                in_tok, out_tok, total = _extract_usage(resp)

                accuracy = "exact" if (in_tok is not None and out_tok is not None) else "unknown"
                in_cost, out_cost, cost, _price = self.meter.compute_cost(provider, final_model, in_tok, out_tok)
                token_breakdown = _build_token_breakdown(in_tok, out_tok, image_breakdown, audio_breakdown)

                self.meter.record(
                    UsageEvent(
                        provider=provider,
                        model=final_model,
                        token_breakdown=token_breakdown,
                        input_cost_usd=in_cost,
                        output_cost_usd=out_cost,
                        cost_usd=cost,
                        accuracy=accuracy,
                        request_id=request_id,
                        latency_ms=latency_ms,
                        status="ok",
                        metadata={"integration": "litellm", "stream": False},
                    )
                )
                return resp

            # stream=True
            def gen():
                for chunk in resp:
                    last_chunk_holder["last"] = chunk
                    yield chunk

            return _StreamWrapper(gen(), finalize)

        except Exception as e:
            status = "error"
            err_type = type(e).__name__
            err_msg = str(e)
            finalize(error=True)
            raise

    async def acompletion(self, **kwargs: Any):
        """
        Mirrors litellm.acompletion(**kwargs).
        If stream=True, returns an async iterator; event is recorded when stream ends.
        """
        model = kwargs.get("model", "unknown")
        provider = _guess_provider_from_model(model)
        stream = bool(kwargs.get("stream", False))

        # Analyze media in messages
        messages = kwargs.get("messages", [])
        image_breakdown = analyze_images_in_messages(messages, provider)
        audio_breakdown = analyze_audio_in_messages(messages, provider)

        kwargs.setdefault("stream_options", {"include_usage": True})

        t0 = time.time()
        last_chunk_holder: dict[str, Any] = {"last": None}
        status = "ok"
        err_type = None
        err_msg = None
        request_id: Optional[str] = None
        final_model: str = model

        def finalize(error: bool = False) -> None:
            latency_ms = int((time.time() - t0) * 1000)

            resp_or_chunk = last_chunk_holder["last"]
            in_tok = out_tok = total = None

            if resp_or_chunk is not None:
                in_tok, out_tok, total = _extract_usage(resp_or_chunk)
                request_id_local = _get_attr(resp_or_chunk, "id", None)
                nonlocal request_id, final_model
                if request_id is None:
                    request_id = request_id_local
                final_model = _get_attr(resp_or_chunk, "model", final_model) or final_model

            accuracy = "exact" if (in_tok is not None and out_tok is not None) else "unknown"
            in_cost, out_cost, cost, _price = self.meter.compute_cost(provider, final_model, in_tok, out_tok)
            token_breakdown = _build_token_breakdown(in_tok, out_tok, image_breakdown, audio_breakdown)

            event = UsageEvent(
                provider=provider,
                model=final_model,
                token_breakdown=token_breakdown,
                input_cost_usd=in_cost,
                output_cost_usd=out_cost,
                cost_usd=cost,
                accuracy=accuracy,
                request_id=request_id,
                latency_ms=latency_ms,
                status="error" if error else status,
                error_type=err_type,
                error_message=err_msg,
                metadata={"integration": "litellm", "stream": stream, "async": True},
            )
            self.meter.record(event)

        try:
            resp = await self._litellm.acompletion(**kwargs)
            if not stream:
                latency_ms = int((time.time() - t0) * 1000)

                request_id = _get_attr(resp, "id", None)
                final_model = _get_attr(resp, "model", model) or model
                in_tok, out_tok, total = _extract_usage(resp)

                accuracy = "exact" if (in_tok is not None and out_tok is not None) else "unknown"
                in_cost, out_cost, cost, _price = self.meter.compute_cost(provider, final_model, in_tok, out_tok)
                token_breakdown = _build_token_breakdown(in_tok, out_tok, image_breakdown, audio_breakdown)

                self.meter.record(
                    UsageEvent(
                        provider=provider,
                        model=final_model,
                        token_breakdown=token_breakdown,
                        input_cost_usd=in_cost,
                        output_cost_usd=out_cost,
                        cost_usd=cost,
                        accuracy=accuracy,
                        request_id=request_id,
                        latency_ms=latency_ms,
                        status="ok",
                        metadata={"integration": "litellm", "stream": False, "async": True},
                    )
                )
                return resp

            # stream=True (async iterator)
            async def agen():
                async for chunk in resp:
                    last_chunk_holder["last"] = chunk
                    yield chunk

            return _AsyncStreamWrapper(agen(), finalize)

        except Exception as e:
            status = "error"
            err_type = type(e).__name__
            err_msg = str(e)
            finalize(error=True)
            raise

    def image_generation(self, **kwargs: Any):
        """
        Mirrors litellm.image_generation(**kwargs).
        Tracks per-image costs based on size and quality.

        Args:
            model: Model name (e.g., "dall-e-3", "openai/dall-e-3")
            prompt: Text prompt for image generation
            size: Image size (e.g., "1024x1024", "1792x1024")
            quality: Quality level (e.g., "standard", "hd")
            n: Number of images to generate (default 1)
            **kwargs: Additional arguments passed to litellm.image_generation

        Returns:
            ImageResponse from LiteLLM
        """
        model = kwargs.get("model", "unknown")
        provider = _guess_provider_from_model(model)
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        n = kwargs.get("n", 1)

        t0 = time.time()

        try:
            resp = self._litellm.image_generation(**kwargs)
            latency_ms = int((time.time() - t0) * 1000)

            # Calculate cost based on per-image pricing
            cost_usd = None
            accuracy = "unknown"

            pricing = self.meter.pricing.get_image_generation_price(provider, model)
            if pricing is not None:
                price_per_image = pricing.get_price(size, quality)
                if price_per_image is not None:
                    cost_usd = price_per_image * n
                    accuracy = "exact"

            # Build token breakdown for image generation
            token_breakdown = [TokenBreakdown(
                type="image_generation",
                count=n,
            )]

            self.meter.record(
                UsageEvent(
                    provider=provider,
                    model=model,
                    token_breakdown=token_breakdown,
                    cost_usd=cost_usd,
                    accuracy=accuracy,
                    latency_ms=latency_ms,
                    status="ok",
                    metadata={
                        "integration": "litellm",
                        "operation": "image_generation",
                        "size": size,
                        "quality": quality,
                        "n": n,
                    },
                )
            )
            return resp

        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            self.meter.record(
                UsageEvent(
                    provider=provider,
                    model=model,
                    token_breakdown=[TokenBreakdown(type="image_generation", count=n)],
                    latency_ms=latency_ms,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    metadata={
                        "integration": "litellm",
                        "operation": "image_generation",
                        "size": size,
                        "quality": quality,
                        "n": n,
                    },
                )
            )
            raise

    async def aimage_generation(self, **kwargs: Any):
        """
        Async version of image_generation.
        Mirrors litellm.aimage_generation(**kwargs).
        """
        model = kwargs.get("model", "unknown")
        provider = _guess_provider_from_model(model)
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        n = kwargs.get("n", 1)

        t0 = time.time()

        try:
            resp = await self._litellm.aimage_generation(**kwargs)
            latency_ms = int((time.time() - t0) * 1000)

            # Calculate cost based on per-image pricing
            cost_usd = None
            accuracy = "unknown"

            pricing = self.meter.pricing.get_image_generation_price(provider, model)
            if pricing is not None:
                price_per_image = pricing.get_price(size, quality)
                if price_per_image is not None:
                    cost_usd = price_per_image * n
                    accuracy = "exact"

            token_breakdown = [TokenBreakdown(
                type="image_generation",
                count=n,
            )]

            self.meter.record(
                UsageEvent(
                    provider=provider,
                    model=model,
                    token_breakdown=token_breakdown,
                    cost_usd=cost_usd,
                    accuracy=accuracy,
                    latency_ms=latency_ms,
                    status="ok",
                    metadata={
                        "integration": "litellm",
                        "operation": "image_generation",
                        "size": size,
                        "quality": quality,
                        "n": n,
                        "async": True,
                    },
                )
            )
            return resp

        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            self.meter.record(
                UsageEvent(
                    provider=provider,
                    model=model,
                    token_breakdown=[TokenBreakdown(type="image_generation", count=n)],
                    latency_ms=latency_ms,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    metadata={
                        "integration": "litellm",
                        "operation": "image_generation",
                        "size": size,
                        "quality": quality,
                        "n": n,
                        "async": True,
                    },
                )
            )
            raise
