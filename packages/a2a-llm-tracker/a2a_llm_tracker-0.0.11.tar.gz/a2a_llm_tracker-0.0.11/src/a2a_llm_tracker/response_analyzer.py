"""
Response analyzer for tracking LLM responses from different providers.

This module allows you to analyze raw LLM responses (from OpenAI, Gemini, Anthropic, etc.)
and record them to the tracker without using the LiteLLM proxy.

Usage:
    from a2a_llm_tracker import get_meter, analyze_response, ResponseType

    # Analyze an OpenAI response
    event = analyze_response(
        response=openai_response,
        response_type=ResponseType.OPENAI,
        meter=get_meter(),
    )

    # Or analyze a Gemini response
    event = analyze_response(
        response=gemini_response,
        response_type=ResponseType.GEMINI,
        meter=get_meter(),
    )
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from .events import TokenBreakdown, UsageEvent, utcnow
from .meter import Meter


class ResponseType(str, Enum):
    """Supported LLM provider response types."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    MISTRAL = "mistral"
    GROQ = "groq"
    TOGETHER = "together"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    LITELLM = "litellm"  # LiteLLM normalized response
    UNKNOWN = "unknown"


@dataclass
class AnalysisResult:
    """Result of analyzing an LLM response."""
    provider: str
    model: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    finish_reason: Optional[str]
    request_id: Optional[str]
    latency_ms: Optional[int]
    raw_usage: Optional[Dict[str, Any]]
    extra_metadata: Dict[str, Any]


def _extract_openai_usage(response: Any) -> AnalysisResult:
    """Extract usage from OpenAI response format."""
    # Handle both dict and object responses
    if isinstance(response, dict):
        usage = response.get("usage", {})
        model = response.get("model", "")
        request_id = response.get("id", None)
        choices = response.get("choices", [])
        finish_reason = choices[0].get("finish_reason") if choices else None
    else:
        # Object response (e.g., from openai SDK)
        usage = getattr(response, "usage", None) or {}
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        elif hasattr(usage, "__dict__"):
            usage = vars(usage)
        model = getattr(response, "model", "")
        request_id = getattr(response, "id", None)
        choices = getattr(response, "choices", [])
        finish_reason = getattr(choices[0], "finish_reason", None) if choices else None

    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")

    # Handle cached tokens if present
    cached_tokens = None
    if isinstance(usage, dict):
        prompt_details = usage.get("prompt_tokens_details", {})
        if prompt_details:
            cached_tokens = prompt_details.get("cached_tokens")

    extra_metadata = {}
    if cached_tokens:
        extra_metadata["cached_tokens"] = cached_tokens

    return AnalysisResult(
        provider="openai",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=finish_reason,
        request_id=request_id,
        latency_ms=None,
        raw_usage=usage if isinstance(usage, dict) else None,
        extra_metadata=extra_metadata,
    )


def _extract_gemini_usage(response: Any) -> AnalysisResult:
    """Extract usage from Google Gemini response format."""
    # Handle both dict and object responses
    if isinstance(response, dict):
        usage_metadata = response.get("usageMetadata", response.get("usage_metadata", {}))
        model = response.get("model", response.get("modelVersion", ""))
        candidates = response.get("candidates", [])
        finish_reason = None
        if candidates:
            finish_reason = candidates[0].get("finishReason", candidates[0].get("finish_reason"))
    else:
        # Object response (e.g., from google-generativeai SDK)
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata and hasattr(usage_metadata, "__dict__"):
            usage_metadata = vars(usage_metadata)
        elif usage_metadata is None:
            usage_metadata = {}
        model = getattr(response, "model", "") or getattr(response, "model_version", "")
        candidates = getattr(response, "candidates", [])
        finish_reason = None
        if candidates:
            finish_reason = getattr(candidates[0], "finish_reason", None)

    # Gemini uses different field names
    input_tokens = usage_metadata.get("promptTokenCount", usage_metadata.get("prompt_token_count"))
    output_tokens = usage_metadata.get("candidatesTokenCount", usage_metadata.get("candidates_token_count"))
    total_tokens = usage_metadata.get("totalTokenCount", usage_metadata.get("total_token_count"))

    # Calculate total if not present
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return AnalysisResult(
        provider="gemini",
        model=model if model else "gemini",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=str(finish_reason) if finish_reason else None,
        request_id=None,
        latency_ms=None,
        raw_usage=usage_metadata if isinstance(usage_metadata, dict) else None,
        extra_metadata={},
    )


def _extract_anthropic_usage(response: Any) -> AnalysisResult:
    """Extract usage from Anthropic response format."""
    # Handle both dict and object responses
    if isinstance(response, dict):
        usage = response.get("usage", {})
        model = response.get("model", "")
        request_id = response.get("id", None)
        stop_reason = response.get("stop_reason")
    else:
        # Object response (e.g., from anthropic SDK)
        usage = getattr(response, "usage", None) or {}
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        elif hasattr(usage, "__dict__"):
            usage = vars(usage)
        model = getattr(response, "model", "")
        request_id = getattr(response, "id", None)
        stop_reason = getattr(response, "stop_reason", None)

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    # Handle cache read/write tokens if present
    extra_metadata = {}
    cache_read = usage.get("cache_read_input_tokens")
    cache_creation = usage.get("cache_creation_input_tokens")
    if cache_read:
        extra_metadata["cache_read_input_tokens"] = cache_read
    if cache_creation:
        extra_metadata["cache_creation_input_tokens"] = cache_creation

    return AnalysisResult(
        provider="anthropic",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=stop_reason,
        request_id=request_id,
        latency_ms=None,
        raw_usage=usage if isinstance(usage, dict) else None,
        extra_metadata=extra_metadata,
    )


def _extract_cohere_usage(response: Any) -> AnalysisResult:
    """Extract usage from Cohere response format."""
    if isinstance(response, dict):
        meta = response.get("meta", {})
        billed_units = meta.get("billed_units", {})
        tokens = meta.get("tokens", {})
        model = response.get("model", "")
        finish_reason = response.get("finish_reason")
    else:
        meta = getattr(response, "meta", None) or {}
        if hasattr(meta, "__dict__"):
            meta = vars(meta)
        billed_units = meta.get("billed_units", {})
        tokens = meta.get("tokens", {})
        model = getattr(response, "model", "")
        finish_reason = getattr(response, "finish_reason", None)

    # Cohere provides both billed_units and tokens
    input_tokens = tokens.get("input_tokens") or billed_units.get("input_tokens")
    output_tokens = tokens.get("output_tokens") or billed_units.get("output_tokens")
    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return AnalysisResult(
        provider="cohere",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=finish_reason,
        request_id=None,
        latency_ms=None,
        raw_usage={"meta": meta} if meta else None,
        extra_metadata={},
    )


def _extract_mistral_usage(response: Any) -> AnalysisResult:
    """Extract usage from Mistral response format (similar to OpenAI)."""
    # Mistral uses OpenAI-compatible format
    result = _extract_openai_usage(response)
    result.provider = "mistral"
    return result


def _extract_groq_usage(response: Any) -> AnalysisResult:
    """Extract usage from Groq response format (OpenAI-compatible)."""
    result = _extract_openai_usage(response)
    result.provider = "groq"

    # Groq provides additional timing info in x_groq
    if isinstance(response, dict):
        x_groq = response.get("x_groq", {})
        usage = x_groq.get("usage", {})
        if usage:
            queue_time = usage.get("queue_time")
            prompt_time = usage.get("prompt_time")
            completion_time = usage.get("completion_time")
            total_time = usage.get("total_time")
            if total_time:
                result.latency_ms = int(total_time * 1000)
            result.extra_metadata.update({
                k: v for k, v in {
                    "queue_time": queue_time,
                    "prompt_time": prompt_time,
                    "completion_time": completion_time,
                }.items() if v is not None
            })

    return result


def _extract_together_usage(response: Any) -> AnalysisResult:
    """Extract usage from Together AI response format (OpenAI-compatible)."""
    result = _extract_openai_usage(response)
    result.provider = "together"
    return result


def _extract_bedrock_usage(response: Any) -> AnalysisResult:
    """Extract usage from AWS Bedrock response format."""
    if isinstance(response, dict):
        usage = response.get("usage", {})
        model = response.get("model", response.get("modelId", ""))
        stop_reason = response.get("stopReason", response.get("stop_reason"))
    else:
        usage = getattr(response, "usage", None) or {}
        if hasattr(usage, "__dict__"):
            usage = vars(usage)
        model = getattr(response, "model", "") or getattr(response, "modelId", "")
        stop_reason = getattr(response, "stopReason", None) or getattr(response, "stop_reason", None)

    input_tokens = usage.get("inputTokens", usage.get("input_tokens"))
    output_tokens = usage.get("outputTokens", usage.get("output_tokens"))
    total_tokens = usage.get("totalTokens", usage.get("total_tokens"))

    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return AnalysisResult(
        provider="bedrock",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=stop_reason,
        request_id=None,
        latency_ms=None,
        raw_usage=usage if isinstance(usage, dict) else None,
        extra_metadata={},
    )


def _extract_vertex_usage(response: Any) -> AnalysisResult:
    """Extract usage from Google Vertex AI response format."""
    # Vertex AI uses similar format to Gemini
    result = _extract_gemini_usage(response)
    result.provider = "vertex"
    return result


def _extract_litellm_usage(response: Any) -> AnalysisResult:
    """Extract usage from LiteLLM normalized response format."""
    # LiteLLM normalizes to OpenAI format
    result = _extract_openai_usage(response)

    # But we can try to get the original provider
    if isinstance(response, dict):
        # LiteLLM often includes the original provider in _hidden_params or model name
        model = response.get("model", "")
    else:
        model = getattr(response, "model", "")

    # Try to extract provider from model name (e.g., "openai/gpt-4o")
    if "/" in model:
        result.provider = model.split("/")[0]
    else:
        result.provider = "litellm"

    return result


def _extract_unknown_usage(response: Any) -> AnalysisResult:
    """Try to extract usage from unknown response format using common patterns."""
    input_tokens = None
    output_tokens = None
    total_tokens = None
    model = ""

    if isinstance(response, dict):
        # Try common usage field names
        usage = response.get("usage", response.get("usageMetadata", response.get("meta", {})))
        if isinstance(usage, dict):
            # OpenAI-style
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", usage.get("promptTokenCount")))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens", usage.get("candidatesTokenCount")))
            total_tokens = usage.get("total_tokens", usage.get("totalTokenCount"))

        model = response.get("model", response.get("modelId", ""))
    else:
        # Try object attributes
        usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
        if usage:
            if hasattr(usage, "__dict__"):
                usage = vars(usage)
            if isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
                output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
                total_tokens = usage.get("total_tokens")

        model = getattr(response, "model", "")

    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return AnalysisResult(
        provider="unknown",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        finish_reason=None,
        request_id=None,
        latency_ms=None,
        raw_usage=None,
        extra_metadata={},
    )


# Mapping of response types to extraction functions
_EXTRACTORS = {
    ResponseType.OPENAI: _extract_openai_usage,
    ResponseType.GEMINI: _extract_gemini_usage,
    ResponseType.ANTHROPIC: _extract_anthropic_usage,
    ResponseType.COHERE: _extract_cohere_usage,
    ResponseType.MISTRAL: _extract_mistral_usage,
    ResponseType.GROQ: _extract_groq_usage,
    ResponseType.TOGETHER: _extract_together_usage,
    ResponseType.BEDROCK: _extract_bedrock_usage,
    ResponseType.VERTEX: _extract_vertex_usage,
    ResponseType.LITELLM: _extract_litellm_usage,
    ResponseType.UNKNOWN: _extract_unknown_usage,
}


def analyze_response(
    response: Any,
    response_type: Union[ResponseType, str],
    meter: Meter,
    *,
    model_override: Optional[str] = None,
    latency_ms: Optional[int] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    record: bool = True,
) -> UsageEvent:
    """
    Analyze an LLM response and optionally record it to the meter's sinks.

    This function extracts usage information from raw LLM provider responses
    and creates a UsageEvent. It supports responses from OpenAI, Gemini,
    Anthropic, Cohere, Mistral, Groq, Together AI, AWS Bedrock, and more.

    Args:
        response: The raw response from the LLM provider (dict or SDK response object)
        response_type: The type of response (ResponseType enum or string like "openai", "gemini")
        meter: The Meter instance to use for cost calculation and recording
        model_override: Override the model name extracted from the response
        latency_ms: Request latency in milliseconds (if known)
        agent_id: Agent ID for attribution
        user_id: User ID for attribution
        session_id: Session ID for attribution
        trace_id: Trace ID for attribution
        metadata: Additional metadata to include in the event
        record: If True (default), record the event to the meter's sinks (including CCS)

    Returns:
        UsageEvent: The created usage event

    Example:
        from a2a_llm_tracker import get_meter, analyze_response, ResponseType
        import openai

        # Make a direct OpenAI call
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Analyze and record the response
        event = analyze_response(
            response=response,
            response_type=ResponseType.OPENAI,
            meter=get_meter(),
            agent_id="my-agent",
        )

        # Or with Gemini
        import google.generativeai as genai
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello!")

        event = analyze_response(
            response=response,
            response_type=ResponseType.GEMINI,
            meter=get_meter(),
        )
    """
    # Convert string to ResponseType if needed
    if isinstance(response_type, str):
        try:
            response_type = ResponseType(response_type.lower())
        except ValueError:
            response_type = ResponseType.UNKNOWN

    # Get the appropriate extractor
    extractor = _EXTRACTORS.get(response_type, _extract_unknown_usage)

    # Extract usage information
    result = extractor(response)

    # Use model override if provided
    model = model_override or result.model
    provider = result.provider

    # Ensure model has provider prefix for pricing lookup
    if model and "/" not in model:
        model = f"{provider}/{model}"

    # Compute cost
    input_cost, output_cost, total_cost, price = meter.compute_cost(
        provider=provider,
        model=model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )

    # Determine accuracy
    accuracy = "exact" if result.input_tokens is not None and result.output_tokens is not None else "unknown"

    # Build token breakdown
    token_breakdown = []
    if result.input_tokens is not None or result.output_tokens is not None:
        token_breakdown.append(TokenBreakdown(
            type="text",
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ))

    # Build metadata
    event_metadata = metadata.copy() if metadata else {}
    if result.finish_reason:
        event_metadata["finish_reason"] = result.finish_reason
    if result.raw_usage:
        event_metadata["raw_usage"] = result.raw_usage
    if result.extra_metadata:
        event_metadata.update(result.extra_metadata)

    # Create the usage event
    event = UsageEvent(
        provider=provider,
        model=model,
        token_breakdown=token_breakdown,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        cost_usd=total_cost,
        accuracy=accuracy,
        request_id=result.request_id,
        latency_ms=latency_ms or result.latency_ms,
        status="ok",
        ts=utcnow(),
        agent_id=agent_id,
        user_id=user_id,
        session_id=session_id,
        trace_id=trace_id,
        metadata=event_metadata,
    )

    # Record to sinks if requested
    if record:
        meter.record(event)

    return event


async def analyze_response_async(
    response: Any,
    response_type: Union[ResponseType, str],
    meter: Meter,
    *,
    model_override: Optional[str] = None,
    latency_ms: Optional[int] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    record: bool = True,
) -> UsageEvent:
    """
    Async version of analyze_response.

    Same as analyze_response but uses async write for CCS sink.
    Use this when calling from async code for better performance.

    See analyze_response for full documentation.
    """
    # The analysis itself is sync, just the recording might benefit from async
    event = analyze_response(
        response=response,
        response_type=response_type,
        meter=meter,
        model_override=model_override,
        latency_ms=latency_ms,
        agent_id=agent_id,
        user_id=user_id,
        session_id=session_id,
        trace_id=trace_id,
        metadata=metadata,
        record=False,  # Don't record sync, we'll do it async
    )

    # Record async if requested
    if record:
        from .context import get_context

        # Enrich with context if missing
        ctx = get_context()
        event.agent_id = event.agent_id or ctx.agent_id
        event.user_id = event.user_id or ctx.user_id
        event.session_id = event.session_id or ctx.session_id
        event.trace_id = event.trace_id or ctx.trace_id

        if meter.project:
            event.metadata.setdefault("project", meter.project)

        # Write to all sinks, using async where available
        for sink in meter.sinks:
            if hasattr(sink, "awrite"):
                await sink.awrite(event)
            else:
                sink.write(event)

    return event
