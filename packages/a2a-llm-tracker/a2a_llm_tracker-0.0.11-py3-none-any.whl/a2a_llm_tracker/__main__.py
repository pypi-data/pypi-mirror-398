"""
Manual smoke-test runner for a2a_llm_tracker.

Usage:
  # Local testing (JSONL sink)
  OPENAI_API_KEY=... python -m a2a_llm_tracker

  # CCS sync testing (requires mftsccs credentials)
  OPENAI_API_KEY=... CLIENT_ID=... CLIENT_SECRET=... python -m a2a_llm_tracker --ccs

Examples include:
  - Text completion (sync/async, streaming/non-streaming)
  - Image analysis (vision)
  - Audio analysis (requires gpt-4o-audio-preview)
  - Image generation (DALL-E)
  - CCS sync (mftsccs integration)
"""

import asyncio
import base64
import os
import sys

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Local Testing Setup (JSONL sink)
# =============================================================================


def setup_local_meter():
    """Setup meter with local JSONL sink for testing."""
    from a2a_llm_tracker import Meter, PricingRegistry
    from a2a_llm_tracker.integrations.litellm import LiteLLM
    from a2a_llm_tracker.sinks.jsonl import JSONLSink

    pricing = PricingRegistry()

    # Example prices - adjust as needed
    pricing.set_price(
        provider="openai",
        model="openai/gpt-4.1",
        input_per_million=2.0,
        output_per_million=8.0,
    )
    pricing.set_price(
        provider="openai",
        model="openai/gpt-4o",
        input_per_million=2.5,
        output_per_million=10.0,
    )
    pricing.set_price(
        provider="openai",
        model="openai/gpt-4o-audio-preview",
        input_per_million=2.5,
        output_per_million=10.0,
    )

    # Image generation pricing (per-image, not per-token)
    pricing.set_image_generation_price(
        provider="openai",
        model="openai/dall-e-3",
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
        provider="openai",
        model="openai/dall-e-2",
        prices={
            "1024x1024": 0.020,
            "512x512": 0.018,
            "256x256": 0.016,
            "default": 0.020,
        }
    )

    meter = Meter(
        pricing=pricing,
        sinks=[JSONLSink("debug_usage.jsonl")],
        project="agent-meter-smoke-test",
    )

    return LiteLLM(meter=meter)


async def query_ccs():
    """
    Setup meter with CCS sink for testing mftsccs integration.

    Requires environment variables:
    - CLIENT_ID: mftsccs client ID (authentication)
    - CLIENT_SECRET: mftsccs client secret (authentication)
    """
    from a2a_llm_tracker import init, get_llm

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET environment variables are required for CCS testing.\n"
            "Set them in your .env file or export them."
        )

    print(f"Initializing CCS with CLIENT_ID: {client_id[:10]}...")

    await init(
        client_id=client_id,
        client_secret=client_secret,
        application_name="a2a-llm-tracker-test",
    )

    from a2a_llm_tracker.sources import CCSSource
    source = CCSSource(int(client_id))
    usage = await source.count_cost()
    counttoken = await source.count_total_tokens()
    print("this is the total usage", usage, counttoken)





# =============================================================================
# CCS Sync Testing Setup
# =============================================================================


async def setup_ccs_meter():
    """
    Setup meter with CCS sink for testing mftsccs integration.

    Requires environment variables:
    - CLIENT_ID: mftsccs client ID (authentication)
    - CLIENT_SECRET: mftsccs client secret (authentication)
    """
    from a2a_llm_tracker import init, get_llm

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET environment variables are required for CCS testing.\n"
            "Set them in your .env file or export them."
        )

    print(f"Initializing CCS with CLIENT_ID: {client_id[:10]}...")

    meter = await init(
        client_id=client_id,
        client_secret=client_secret,
        application_name="a2a-llm-tracker-test",
    )
    #concept = await GetTheConcept(int(client_id))
    #print("CCS initialized successfully!", concept)
    return get_llm(meter)


async def get_ccs_meter():
    """
    Setup meter with CCS sink for testing mftsccs integration.

    Requires environment variables:
    - CLIENT_ID: mftsccs client ID (authentication)
    - CLIENT_SECRET: mftsccs client secret (authentication)
    """
    from a2a_llm_tracker import init, get_llm

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET environment variables are required for CCS testing.\n"
            "Set them in your .env file or export them."
        )

    print(f"Initializing CCS with CLIENT_ID: {client_id[:10]}...")

    meter = await init(
        client_id=client_id,
        client_secret=client_secret,
        application_name="a2a-llm-tracker-test",
    )
    return meter

async def run_ccs_test():
    """
    Run a simple test using the CCS sink.

    This will:
    1. Initialize mftsccs with credentials
    2. Create the_llm_tracker concept
    3. Make a completion request
    4. Create the_llm_usage concept with all tracking data
    5. Connect concepts together
    """
    print("\n" + "=" * 50)
    print("CCS SYNC TEST")
    print("=" * 50)

    try:
        llm = await setup_ccs_meter()

        print("\n=== Making completion request ===")
        resp = llm.completion(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Say 'CCS sync test successful!' in one sentence."}],
        )


        content = resp.choices[0].message.content
        
        print(f"Response: {content}")

        # Give async tasks time to complete
        print("\nWaiting for CCS sync to complete...")
        await asyncio.sleep(2)

        print("\n" + "=" * 50)
        print("CCS sync test complete!")
        print("Check BoomConsole for:")
        print("  - the_llm_tracker concept (application)")
        print("  - the_llm_usage concept (usage data)")
        print("  - the_llm_provider concept (openai)")
        print("  - the_llm_model concept (gpt-4o)")
        print("=" * 50)

    except ImportError as e:
        print(f"\nCCS test skipped: {e}")
        print("Install mftsccs with: pip install mftsccs")
    except Exception as e:
        print(f"\nCCS test failed: {e}")
        raise


# =============================================================================
# Text Examples
# =============================================================================


def run_sync(llm) -> None:
    print("\n=== SYNC NON-STREAMING ===")
    resp = llm.completion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
    )
    print(resp)


def run_stream(llm) -> None:
    print("\n=== SYNC STREAMING ===")
    for chunk in llm.completion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Write a short haiku about testing."}],
        stream=True,
    ):
        print(chunk, end="", flush=True)
    print()


async def run_async(llm) -> None:
    print("\n=== ASYNC NON-STREAMING ===")
    resp = await llm.acompletion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Async hello!"}],
    )
    print(resp)


async def run_async_stream(llm) -> None:
    print("\n=== ASYNC STREAMING ===")
    stream = await llm.acompletion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Stream something async."}],
        stream=True,
    )
    async for chunk in stream:
        print(chunk, end="", flush=True)
    print()


# =============================================================================
# Image Example
# =============================================================================


def create_sample_image_base64() -> str:
    """
    Create a simple 2x2 red PNG image for testing.
    In real usage, you would load an actual image file.
    """
    # Minimal valid PNG: 2x2 red pixels
    # This is a pre-encoded tiny PNG for demonstration
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02,  # 2x2 pixels
        0x08, 0x02, 0x00, 0x00, 0x00, 0xFD, 0xD4, 0x9A,
        0x73, 0x00, 0x00, 0x00, 0x14, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x78, 0x9C, 0x62, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x00, 0xFF, 0xFF, 0x03, 0x00, 0x05,
        0xFE, 0x02, 0xFE, 0xA3, 0x56, 0x5A, 0x09, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
        0x42, 0x60, 0x82
    ])
    return base64.b64encode(png_data).decode("utf-8")


def run_image_example(llm) -> None:
    """
    Example: Send an image to a vision model.

    The tracker will automatically:
    1. Detect the image in the message
    2. Parse dimensions from the base64 data
    3. Estimate token usage based on image size
    4. Record it in the token_breakdown as type="image"
    """
    print("\n=== IMAGE EXAMPLE (Vision) ===")

    # Create a sample image (in practice, load a real image)
    image_b64 = create_sample_image_base64()

    resp = llm.completion(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image? Reply in one word."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                            "detail": "low"  # "low", "high", or "auto"
                        }
                    }
                ]
            }
        ],
    )
    print(f"Response: {resp.choices[0].message.content}")
    print("(Check debug_usage.jsonl for token_breakdown with type='image')")


def run_image_url_example(llm) -> None:
    """
    Example: Send an image URL to a vision model.

    Note: For URL-based images, we can't determine dimensions without
    fetching, so token estimation uses default assumptions.
    """
    print("\n=== IMAGE URL EXAMPLE ===")

    resp = llm.completion(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image briefly."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/300px-PNG_transparency_demonstration_1.png"
                        }
                    }
                ]
            }
        ],
    )
    print(f"Response: {resp.choices[0].message.content}")


# =============================================================================
# Audio Example
# =============================================================================


def create_sample_audio_base64() -> str:
    """
    Create a minimal WAV file for testing.
    This is a 0.1 second silent audio clip.
    In real usage, you would load an actual audio file.
    """
    import struct

    # WAV file parameters
    sample_rate = 16000
    num_channels = 1
    bits_per_sample = 16
    duration_seconds = 0.1
    num_samples = int(sample_rate * duration_seconds)

    # Generate silence (all zeros)
    audio_data = b'\x00\x00' * num_samples

    # Build WAV header
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(audio_data)
    file_size = 36 + data_size

    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        file_size,
        b'WAVE',
        b'fmt ',
        16,  # fmt chunk size
        1,   # PCM format
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )

    wav_bytes = wav_header + audio_data
    return base64.b64encode(wav_bytes).decode("utf-8")


def run_audio_example(llm) -> None:
    """
    Example: Send audio to an audio-capable model.

    The tracker will automatically:
    1. Detect the audio in the message
    2. Parse duration from WAV/MP3 headers
    3. Estimate token usage (~40 tokens/second for OpenAI)
    4. Record it in the token_breakdown as type="audio"

    Note: Requires gpt-4o-audio-preview or similar audio-capable model.
    """
    print("\n=== AUDIO EXAMPLE ===")

    # Create a sample audio clip
    audio_b64 = create_sample_audio_base64()

    try:
        resp = llm.completion(
            model="openai/gpt-4o-audio-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you hear in this audio?"},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ],
        )
        print(f"Response: {resp.choices[0].message.content}")
        print("(Check debug_usage.jsonl for token_breakdown with type='audio')")
    except Exception as e:
        print(f"Audio example skipped: {e}")
        print("(Audio requires gpt-4o-audio-preview model access)")


# =============================================================================
# Image Generation Example
# =============================================================================


def run_image_generation_example(llm) -> None:
    """
    Example: Generate an image using DALL-E.

    The tracker will automatically:
    1. Track the image generation request
    2. Calculate cost based on per-image pricing (size + quality)
    3. Record it in the token_breakdown as type="image_generation"

    Note: Unlike vision/audio, image generation is priced per-image, not per-token.
    """
    print("\n=== IMAGE GENERATION EXAMPLE (DALL-E) ===")

    try:
        resp = llm.image_generation(
            model="openai/dall-e-3",
            prompt="A cute robot cat sitting on a rainbow, digital art style",
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # The response contains the generated image URL(s)
        if resp.data and len(resp.data) > 0:
            print(f"Generated image URL: {resp.data[0].url[:80]}...")
        print("(Check debug_usage.jsonl for token_breakdown with type='image_generation')")
        print("Expected cost: $0.040 (1024x1024 standard)")

    except Exception as e:
        print(f"Image generation example skipped: {e}")
        print("(Requires DALL-E API access)")


def run_image_generation_hd_example(llm) -> None:
    """
    Example: Generate an HD image using DALL-E 3.

    HD quality costs more than standard quality.
    """
    print("\n=== IMAGE GENERATION HD EXAMPLE ===")

    try:
        resp = llm.image_generation(
            model="openai/dall-e-3",
            prompt="A majestic mountain landscape at sunset, photorealistic",
            size="1792x1024",  # Wide format
            quality="hd",      # HD quality
            n=1,
        )

        if resp.data and len(resp.data) > 0:
            print(f"Generated HD image URL: {resp.data[0].url[:80]}...")
        print("Expected cost: $0.120 (1792x1024 hd)")

    except Exception as e:
        print(f"HD image generation skipped: {e}")


# =============================================================================
# Multi-modal Example
# =============================================================================


def run_multimodal_example(llm) -> None:
    """
    Example: Send both image and text in the same message.

    The token_breakdown will contain:
    - type="text" with provider-reported tokens
    - type="image" with estimated image tokens
    """
    print("\n=== MULTI-MODAL EXAMPLE (Text + Image) ===")

    image_b64 = create_sample_image_base64()

    resp = llm.completion(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Is this image red, green, or blue? Just say the color."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ],
    )

    print(f"Response: {resp.choices[0].message.content}")
    print("\nExpected token_breakdown structure:")
    print('  [{"type": "text", "input_tokens": X, "output_tokens": Y},')
    print('   {"type": "image", "input_tokens": 85, "count": 1}]')


# =============================================================================
# Main Entry Points
# =============================================================================



async def llm_test():
    from openai import OpenAI
    from a2a_llm_tracker import get_meter, analyze_response, ResponseType
    load_dotenv()
    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert researcher who carefully analyzes web content "
                    "to build comprehensive profiles of individuals. You extract nuanced "
                    "information that automated parsers miss. Always respond with valid JSON."
                ),
            },
            {"role": "user", "content": "say hi"},
        ],
        temperature=0.1,
        max_tokens=1500,
        )
    meter = await get_ccs_meter()
    analyze_response(response=response, response_type=ResponseType.OPENAI, meter = meter, agent_id = "my-agent")
def run_local_tests():
    """Run all tests with local JSONL sink."""
    from a2a_llm_tracker import meter_context

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Exiting.")
        return

    llm = setup_local_meter()

    with meter_context(agent_id="smoke-test-agent", session_id="local"):
        # Basic text examples
        run_sync(llm)
        run_stream(llm)
        asyncio.run(run_async(llm))
        asyncio.run(run_async_stream(llm))

        # Image examples (requires gpt-4o or similar vision model)
        try:
            run_image_example(llm)
            run_multimodal_example(llm)
        except Exception as e:
            print(f"\nImage examples skipped: {e}")

        # Audio example (requires gpt-4o-audio-preview)
        run_audio_example(llm)

        # Image generation examples (requires DALL-E access)
        run_image_generation_example(llm)
        run_image_generation_hd_example(llm)

    print("\n" + "=" * 50)
    print("Local smoke test complete!")
    print("Check debug_usage.jsonl for token breakdowns.")
    print("=" * 50)


def main() -> None:
    """Main entry point."""
    # Check for --ccs flag
    if "--ccs" in sys.argv:
        print("Running CCS sync test...")
        asyncio.run(run_ccs_test())
    elif "--analyze" in sys.argv:
        asyncio.run(llm_test())
    elif "--output" in sys.argv:
        asyncio.run(query_ccs())
    else:
        print("Running local tests (use --ccs for CCS sync test)...")
        run_local_tests()


if __name__ == "__main__":
    main()
