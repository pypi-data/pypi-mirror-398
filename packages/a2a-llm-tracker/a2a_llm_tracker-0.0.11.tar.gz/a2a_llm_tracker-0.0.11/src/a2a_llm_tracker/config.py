"""
Global configuration and initialization for a2a_llm_tracker.

Usage:
    from a2a_llm_tracker import init, get_llm

    # Initialize with credentials (sync - no async needed!)
    meter = init(
        client_id="your-client-id",
        client_secret="your-client-secret",
        application_name="my-chatbot",
    )

    # Then get the configured LiteLLM wrapper
    llm = get_llm(meter)
    resp = llm.completion(model="openai/gpt-4o", messages=[...])
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional, Union

from .meter import Meter
from .pricing import PricingRegistry
from ccs import init as ccs_init, CCSConfig

# Global state
_meter: Optional[Meter] = None
_initialized: bool = False
_ccs_client: Any = None  # mftsccs client instance


class TrackerNotInitializedError(Exception):
    """Raised when trying to use the tracker before calling init()."""
    pass


def _create_openai_pricing() -> PricingRegistry:
    """Create a PricingRegistry with OpenAI default prices (as of Dec 2024)."""
    pricing = PricingRegistry()

    # GPT-4o models
    pricing.set_price("openai", "openai/gpt-4o", input_per_million=2.50, output_per_million=10.00)
    pricing.set_price("openai", "openai/gpt-4o-mini", input_per_million=0.15, output_per_million=0.60)
    pricing.set_price("openai", "openai/gpt-4o-audio-preview", input_per_million=2.50, output_per_million=10.00)

    # GPT-4.1 models
    pricing.set_price("openai", "openai/gpt-4.1", input_per_million=2.00, output_per_million=8.00)
    pricing.set_price("openai", "openai/gpt-4.1-mini", input_per_million=0.40, output_per_million=1.60)
    pricing.set_price("openai", "openai/gpt-4.1-nano", input_per_million=0.10, output_per_million=0.40)

    # GPT-4 Turbo
    pricing.set_price("openai", "openai/gpt-4-turbo", input_per_million=10.00, output_per_million=30.00)

    # GPT-3.5
    pricing.set_price("openai", "openai/gpt-3.5-turbo", input_per_million=0.50, output_per_million=1.50)

    # o1 reasoning models
    pricing.set_price("openai", "openai/o1", input_per_million=15.00, output_per_million=60.00)
    pricing.set_price("openai", "openai/o1-mini", input_per_million=1.10, output_per_million=4.40)
    pricing.set_price("openai", "openai/o1-pro", input_per_million=150.00, output_per_million=600.00)

    # o3 reasoning models
    pricing.set_price("openai", "openai/o3-mini", input_per_million=1.10, output_per_million=4.40)

    # Image generation
    pricing.set_image_generation_price(
        "openai", "openai/dall-e-3",
        prices={
            "1024x1024:standard": 0.040,
            "1024x1024:hd": 0.080,
            "1792x1024:standard": 0.080,
            "1792x1024:hd": 0.120,
            "1024x1792:standard": 0.080,
            "1024x1792:hd": 0.120,
            "default": 0.040,
        }
    )
    pricing.set_image_generation_price(
        "openai", "openai/dall-e-2",
        prices={
            "1024x1024": 0.020,
            "512x512": 0.018,
            "256x256": 0.016,
            "default": 0.020,
        }
    )

    return pricing


def _create_anthropic_pricing() -> PricingRegistry:
    """Create a PricingRegistry with Anthropic default prices (as of Dec 2024)."""
    pricing = PricingRegistry()

    # Claude 3.5 models
    pricing.set_price("anthropic", "anthropic/claude-3-5-sonnet-latest", input_per_million=3.00, output_per_million=15.00)
    pricing.set_price("anthropic", "anthropic/claude-3-5-haiku-latest", input_per_million=0.80, output_per_million=4.00)

    # Claude 3 models
    pricing.set_price("anthropic", "anthropic/claude-3-opus-latest", input_per_million=15.00, output_per_million=75.00)
    pricing.set_price("anthropic", "anthropic/claude-3-sonnet-20240229", input_per_million=3.00, output_per_million=15.00)
    pricing.set_price("anthropic", "anthropic/claude-3-haiku-20240307", input_per_million=0.25, output_per_million=1.25)

    return pricing


def _create_combined_pricing() -> PricingRegistry:
    """Create a PricingRegistry with both OpenAI and Anthropic prices."""
    openai = _create_openai_pricing()
    anthropic = _create_anthropic_pricing()

    # Merge anthropic into openai
    for key, price in anthropic._prices.items():
        openai._prices[key] = price

    return openai


def _resolve_pricing(pricing: Union[str, PricingRegistry, None]) -> PricingRegistry:
    """Resolve pricing parameter to a PricingRegistry instance."""
    if pricing is None or pricing == "all" or pricing == "combined" or pricing == "default":
        return _create_combined_pricing()

    if isinstance(pricing, PricingRegistry):
        return pricing

    if isinstance(pricing, str):
        pricing_lower = pricing.lower().strip()
        if pricing_lower == "openai":
            return _create_openai_pricing()
        elif pricing_lower == "anthropic":
            return _create_anthropic_pricing()
        else:
            raise ValueError(f"Unknown pricing preset: {pricing}. Supported: openai, anthropic, all")

    raise TypeError(f"pricing must be str or PricingRegistry, got {type(pricing)}")

async def init(
    client_id: str,
    client_secret: str,
    application_name: str = "",
    server_url:str = "https://boomconsole.com",
    pricing: Union[str, PricingRegistry, None] = "all",
) -> Meter:
    """
    Initialize the a2a_llm_tracker package with mftsccs configuration.

    This must be called before using get_llm() or other tracker features.

    Args:
        client_id: Your mftsccs client ID for authentication
        client_secret: Your mftsccs client secret for authentication
        application_name: Name of your application for attribution
        pricing: Pricing configuration. Can be:
            - "openai": OpenAI default prices
            - "anthropic": Anthropic default prices
            - "all" or "combined": Both OpenAI and Anthropic (default)
            - A PricingRegistry instance for custom pricing
            - None for default pricing

    Returns:
        The configured Meter instance

    Raises:
        ValueError: If already initialized (call reset() first to reinitialize)

    Example:
        import asyncio
        from a2a_llm_tracker import init, get_llm

        async def main():
            await init(
                client_id="your-client-id",
                client_secret="your-client-secret",
                application_name="my-chatbot",
            )

            llm = get_llm()
            response = llm.completion(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Hello!"}]
            )

        asyncio.run(main())
    """
    global _meter, _initialized, _ccs_client

    if _initialized:
        raise ValueError(
            "a2a_llm_tracker is already initialized. "
            "Call reset() first if you want to reinitialize."
        )

    # Initialize mftsccs client with our internal configuration
    try:


        # Build CCSConfig with internal defaults and user credentials
        config = CCSConfig(
            aiUrl="https://ai.freeschema.com",
            accessToken="",
            enableAi=True,
            flags=None,
            parameters=None,
            storagePath=None,
            clientId=client_id,
            clientSecret=client_secret,
        )

        _ccs_client = await ccs_init(
            server_url,
            server_url,
            applicationName=application_name,
            config=config,
        )
    except ImportError:
        raise ImportError(
            "mftsccs is not installed. Install with: pip install mftsccs"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize mftsccs: {e}") from e

    # Resolve pricing
    resolved_pricing = _resolve_pricing(pricing)

    # Create meter with CCS sink
    # Pass client_id as entity_id to connect tracker to that entity
    from .sinks.ccs import CCSSink
    ccs_sink = CCSSink(
        application_name=application_name,
        entity_id=int(client_id),
    )


    _meter = Meter(
        pricing=resolved_pricing,
        sinks=[ccs_sink],
        project=application_name,
    )
    _initialized = True

    return _meter


def init_sync(
    application_name: str = "",
    pricing: Union[str, PricingRegistry, None] = "all",
    local_sink: Optional[str] = None,
) -> Meter:
    """
    Initialize the tracker synchronously without mftsccs (for local development/testing).

    Args:
        application_name: Name of your application for attribution
        pricing: Pricing configuration preset or PricingRegistry
        local_sink: Optional local sink specification (e.g., "jsonl:usage.jsonl")

    Returns:
        The configured Meter instance

    Example:
        from a2a_llm_tracker import init_sync, get_llm

        init_sync(
            application_name="my-chatbot",
            local_sink="jsonl:usage.jsonl",
        )

        llm = get_llm()
    """
    global _meter, _initialized

    if _initialized:
        raise ValueError(
            "a2a_llm_tracker is already initialized. "
            "Call reset() first if you want to reinitialize."
        )

    # Resolve pricing
    resolved_pricing = _resolve_pricing(pricing)

    # Create sinks
    sinks = []
    if local_sink:
        if ":" in local_sink:
            sink_type, path = local_sink.split(":", 1)
        else:
            sink_type = local_sink
            path = None

        sink_type = sink_type.lower().strip()

        if sink_type == "jsonl":
            from .sinks.jsonl import JSONLSink
            sinks.append(JSONLSink(path or "usage.jsonl"))
        elif sink_type == "sqlite":
            from .sinks.sqlite import SQLiteSink
            sinks.append(SQLiteSink(path or "usage.db"))
        elif sink_type == "console":
            from .sinks.console import ConsoleSink
            sinks.append(ConsoleSink())

    _meter = Meter(
        pricing=resolved_pricing,
        sinks=sinks,
        project=application_name,
    )
    _initialized = True

    return _meter


def reset() -> None:
    """
    Reset the global tracker state.

    Call this if you need to reinitialize with different settings.
    """
    global _meter, _initialized, _ccs_client
    _meter = None
    _initialized = False
    _ccs_client = None


def is_initialized() -> bool:
    """Check if the tracker has been initialized."""
    return _initialized


def get_meter() -> Meter:
    """
    Get the global Meter instance.

    Raises:
        TrackerNotInitializedError: If init() has not been called
    """
    if not _initialized or _meter is None:
        raise TrackerNotInitializedError(
            "a2a_llm_tracker is not initialized. "
            "Call init() before using the tracker:\n\n"
            "    from a2a_llm_tracker import init\n"
            "    await init(client_id='...', client_secret='...', application_name='my-app')\n"
        )
    return _meter


def get_ccs_client() -> Any:
    """
    Get the mftsccs client instance.

    Raises:
        TrackerNotInitializedError: If init() has not been called
    """
    if not _initialized or _ccs_client is None:
        raise TrackerNotInitializedError(
            "a2a_llm_tracker is not initialized or was initialized with init_sync(). "
            "Call init() to use mftsccs features."
        )
    return _ccs_client


def get_llm(meter):
    """
    Get a LiteLLM wrapper configured with the global meter.

    Raises:
        TrackerNotInitializedError: If init() has not been called

    Example:
        from a2a_llm_tracker import init, get_llm

        await init(client_id="...", client_secret="...", application_name="my-app")
        llm = get_llm()

        response = llm.completion(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    from .integrations.litellm import LiteLLM
    return LiteLLM(meter=meter)
