"""
Media detection and token estimation utilities.

Provides functions to:
1. Count media (images, audio, video) in LLM message arrays
2. Estimate token usage based on provider-specific rules
3. Return TokenBreakdown objects for unified tracking
"""
from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
from io import BytesIO

from .events import TokenBreakdown


@dataclass
class ImageInfo:
    """Information about an image in a message."""
    width: Optional[int] = None
    height: Optional[int] = None
    detail: str = "auto"  # "low", "high", or "auto"
    source: str = "url"   # "url" or "base64"


@dataclass
class AudioInfo:
    """Information about an audio clip in a message."""
    duration_seconds: Optional[float] = None
    format: str = "unknown"  # "wav", "mp3", "pcm16", etc.
    source: str = "base64"   # "base64" or "url"


def _get_image_dimensions_from_base64(data_url: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract image dimensions from a base64 data URL.
    Returns (width, height) or (None, None) if unable to determine.
    """
    try:
        # Extract base64 data after the comma
        if "," not in data_url:
            return None, None

        b64_data = data_url.split(",", 1)[1]
        image_data = base64.b64decode(b64_data)

        # Try to get dimensions using PIL if available
        try:
            from PIL import Image
            img = Image.open(BytesIO(image_data))
            return img.size  # (width, height)
        except ImportError:
            pass

        # Fallback: parse image headers manually for common formats
        return _parse_image_header(image_data)
    except Exception:
        return None, None


def _parse_image_header(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    """Parse image dimensions from raw bytes (PNG, JPEG, GIF, WebP)."""
    if len(data) < 24:
        return None, None

    # PNG: bytes 16-23 contain width and height as 4-byte big-endian integers
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        width = int.from_bytes(data[16:20], 'big')
        height = int.from_bytes(data[20:24], 'big')
        return width, height

    # JPEG: more complex, need to find SOF marker
    if data[:2] == b'\xff\xd8':
        return _parse_jpeg_dimensions(data)

    # GIF: bytes 6-9 contain width and height as 2-byte little-endian
    if data[:6] in (b'GIF87a', b'GIF89a'):
        width = int.from_bytes(data[6:8], 'little')
        height = int.from_bytes(data[8:10], 'little')
        return width, height

    # WebP: check for RIFF header
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return _parse_webp_dimensions(data)

    return None, None


def _parse_jpeg_dimensions(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    """Parse JPEG dimensions by finding SOF marker."""
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        # SOF markers: 0xC0-0xCF except 0xC4, 0xC8, 0xCC
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height = int.from_bytes(data[i+5:i+7], 'big')
            width = int.from_bytes(data[i+7:i+9], 'big')
            return width, height
        # Skip to next marker
        if i + 3 >= len(data):
            break
        length = int.from_bytes(data[i+2:i+4], 'big')
        i += 2 + length
    return None, None


def _parse_webp_dimensions(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    """Parse WebP dimensions."""
    if len(data) < 30:
        return None, None
    # VP8 lossy
    if data[12:16] == b'VP8 ':
        if len(data) >= 30 and data[23:26] == b'\x9d\x01\x2a':
            width = int.from_bytes(data[26:28], 'little') & 0x3FFF
            height = int.from_bytes(data[28:30], 'little') & 0x3FFF
            return width, height
    # VP8L lossless
    elif data[12:16] == b'VP8L':
        if len(data) >= 25:
            bits = int.from_bytes(data[21:25], 'little')
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height
    return None, None


def _estimate_openai_image_tokens(
    width: Optional[int],
    height: Optional[int],
    detail: str = "auto"
) -> int:
    """
    Estimate tokens for an image using OpenAI's pricing rules.

    OpenAI Vision pricing (as of 2024):
    - low detail: 85 tokens flat
    - high detail:
      - Scale image to fit in 2048x2048
      - Scale shortest side to 768px
      - Count 512x512 tiles, each tile = 170 tokens
      - Add base 85 tokens

    Reference: https://platform.openai.com/docs/guides/vision
    """
    # Default assumption for unknown dimensions
    if width is None or height is None:
        # Assume a typical 1024x1024 image with high detail
        return 765  # 4 tiles * 170 + 85

    if detail == "low":
        return 85

    # High detail calculation
    # Step 1: Scale to fit within 2048x2048
    max_dim = 2048
    if width > max_dim or height > max_dim:
        scale = max_dim / max(width, height)
        width = int(width * scale)
        height = int(height * scale)

    # Step 2: Scale so shortest side is 768px
    min_side = 768
    if min(width, height) > min_side:
        scale = min_side / min(width, height)
        width = int(width * scale)
        height = int(height * scale)

    # Step 3: Count 512x512 tiles
    tiles_x = math.ceil(width / 512)
    tiles_y = math.ceil(height / 512)
    total_tiles = tiles_x * tiles_y

    # Step 4: Calculate tokens
    return (total_tiles * 170) + 85


def _estimate_anthropic_image_tokens(
    width: Optional[int],
    height: Optional[int]
) -> int:
    """
    Estimate tokens for an image using Anthropic's pricing rules.

    Anthropic Vision pricing:
    - ~1,600 tokens per megapixel
    - Images are scaled to fit within limits before counting

    Reference: https://docs.anthropic.com/en/docs/vision
    """
    if width is None or height is None:
        # Default assumption: 1024x1024 ≈ 1 megapixel ≈ 1,600 tokens
        return 1600

    # Calculate megapixels
    megapixels = (width * height) / 1_000_000

    # Anthropic caps at certain resolutions, scale down if needed
    max_pixels = 1.15  # Approximate max megapixels after scaling
    if megapixels > max_pixels:
        megapixels = max_pixels

    return int(megapixels * 1600)


def _estimate_image_tokens(
    image: ImageInfo,
    provider: str
) -> int:
    """Estimate tokens for an image based on provider."""
    provider_lower = provider.lower()

    if "openai" in provider_lower or "gpt" in provider_lower:
        return _estimate_openai_image_tokens(image.width, image.height, image.detail)
    elif "anthropic" in provider_lower or "claude" in provider_lower:
        return _estimate_anthropic_image_tokens(image.width, image.height)
    elif "gemini" in provider_lower or "google" in provider_lower:
        # Gemini uses similar token counting to Anthropic
        return _estimate_anthropic_image_tokens(image.width, image.height)
    else:
        # Default to OpenAI-style estimation
        return _estimate_openai_image_tokens(image.width, image.height, image.detail)


def analyze_images_in_messages(
    messages: List[Any],
    provider: str = "openai"
) -> Optional[TokenBreakdown]:
    """
    Analyze messages to count images and estimate token usage.

    Args:
        messages: List of message dicts (OpenAI/LiteLLM format)
        provider: Provider name for token estimation rules

    Returns:
        TokenBreakdown for images, or None if no images found
    """
    images: List[ImageInfo] = []

    for msg in messages:
        # Handle both dict and object-style messages
        if isinstance(msg, dict):
            content = msg.get("content")
        else:
            content = getattr(msg, "content", None)

        # Skip if content is just a string (no images)
        if not isinstance(content, list):
            continue

        for part in content:
            if not isinstance(part, dict):
                continue

            if part.get("type") != "image_url":
                continue

            image_url_obj = part.get("image_url", {})
            if isinstance(image_url_obj, str):
                # Sometimes it's just the URL string
                url = image_url_obj
                detail = "auto"
            else:
                url = image_url_obj.get("url", "")
                detail = image_url_obj.get("detail", "auto")

            # Determine source type and try to get dimensions
            width, height = None, None
            if url.startswith("data:"):
                source = "base64"
                width, height = _get_image_dimensions_from_base64(url)
            else:
                source = "url"
                # Can't get dimensions from URL without fetching

            images.append(ImageInfo(
                width=width,
                height=height,
                detail=detail,
                source=source
            ))

    if not images:
        return None

    # Calculate estimated tokens
    total_tokens = 0
    for img in images:
        total_tokens += _estimate_image_tokens(img, provider)

    return TokenBreakdown(
        type="image",
        input_tokens=total_tokens,
        count=len(images)
    )


# =============================================================================
# Audio Detection and Token Estimation
# =============================================================================


def _get_audio_duration_from_base64(data_url: str) -> Tuple[Optional[float], str]:
    """
    Extract audio duration from a base64 data URL.
    Returns (duration_seconds, format) or (None, format) if unable to determine duration.
    """
    try:
        # Parse the data URL format: data:audio/wav;base64,<data>
        if "," not in data_url:
            return None, "unknown"

        header, b64_data = data_url.split(",", 1)

        # Extract format from header (e.g., "data:audio/wav;base64" -> "wav")
        audio_format = "unknown"
        if "audio/" in header:
            format_part = header.split("audio/")[1].split(";")[0]
            audio_format = format_part.lower()

        audio_data = base64.b64decode(b64_data)

        # Try to get duration using pydub if available
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(BytesIO(audio_data))
            return len(audio) / 1000.0, audio_format  # pydub returns milliseconds
        except ImportError:
            pass

        # Fallback: parse audio headers manually for common formats
        duration = _parse_audio_header(audio_data, audio_format)
        return duration, audio_format
    except Exception:
        return None, "unknown"


def _parse_audio_header(data: bytes, format_hint: str) -> Optional[float]:
    """Parse audio duration from raw bytes (WAV, MP3)."""
    if len(data) < 44:
        return None

    # WAV format
    if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
        return _parse_wav_duration(data)

    # MP3 format (starts with ID3 tag or frame sync)
    if data[:3] == b'ID3' or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return _parse_mp3_duration(data)

    return None


def _parse_wav_duration(data: bytes) -> Optional[float]:
    """Parse WAV file duration."""
    try:
        # Find 'fmt ' chunk
        fmt_offset = data.find(b'fmt ')
        if fmt_offset == -1:
            return None

        # Read format info (after 'fmt ' and chunk size)
        audio_format = int.from_bytes(data[fmt_offset+8:fmt_offset+10], 'little')
        num_channels = int.from_bytes(data[fmt_offset+10:fmt_offset+12], 'little')
        sample_rate = int.from_bytes(data[fmt_offset+12:fmt_offset+16], 'little')
        byte_rate = int.from_bytes(data[fmt_offset+16:fmt_offset+20], 'little')

        # Find 'data' chunk
        data_offset = data.find(b'data')
        if data_offset == -1:
            return None

        data_size = int.from_bytes(data[data_offset+4:data_offset+8], 'little')

        if byte_rate > 0:
            return data_size / byte_rate
        return None
    except Exception:
        return None


def _parse_mp3_duration(data: bytes) -> Optional[float]:
    """
    Estimate MP3 duration. This is approximate without full parsing.
    For accurate duration, use pydub or similar library.
    """
    try:
        # Skip ID3 tag if present
        offset = 0
        if data[:3] == b'ID3':
            # ID3v2 tag size is in bytes 6-9, syncsafe integer
            size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | \
                   ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
            offset = 10 + size

        # Find first valid frame
        while offset < len(data) - 4:
            if data[offset] == 0xFF and (data[offset + 1] & 0xE0) == 0xE0:
                break
            offset += 1

        if offset >= len(data) - 4:
            return None

        # Parse frame header
        header = int.from_bytes(data[offset:offset+4], 'big')

        # Extract bitrate index and sample rate index
        version = (header >> 19) & 3
        layer = (header >> 17) & 3
        bitrate_idx = (header >> 12) & 0xF
        samplerate_idx = (header >> 10) & 3

        # Bitrate table for MPEG1 Layer III
        bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
        sample_rates = [44100, 48000, 32000, 0]

        if bitrate_idx == 0 or bitrate_idx == 15:
            return None
        if samplerate_idx == 3:
            return None

        bitrate = bitrates[bitrate_idx] * 1000  # kbps to bps

        # Estimate duration from file size and bitrate
        if bitrate > 0:
            # Rough estimate: (file_size * 8) / bitrate
            return (len(data) * 8) / bitrate
        return None
    except Exception:
        return None


def _estimate_openai_audio_tokens(duration_seconds: Optional[float]) -> int:
    """
    Estimate tokens for audio using OpenAI's pricing rules.

    OpenAI Audio pricing (GPT-4o with audio):
    - Audio input: ~40 tokens per second of audio (approximate)
    - This is based on observed usage patterns

    Reference: https://platform.openai.com/docs/guides/audio
    """
    if duration_seconds is None:
        # Default assumption: 10 seconds of audio
        return 400  # 10 seconds * 40 tokens/sec

    return int(duration_seconds * 40)


def _estimate_gemini_audio_tokens(duration_seconds: Optional[float]) -> int:
    """
    Estimate tokens for audio using Google Gemini's pricing rules.

    Gemini Audio:
    - Audio is converted to tokens at ~32 tokens per second

    Reference: https://ai.google.dev/gemini-api/docs/audio
    """
    if duration_seconds is None:
        return 320  # 10 seconds * 32 tokens/sec

    return int(duration_seconds * 32)


def _estimate_audio_tokens(audio: AudioInfo, provider: str) -> int:
    """Estimate tokens for an audio clip based on provider."""
    provider_lower = provider.lower()

    if "openai" in provider_lower or "gpt" in provider_lower:
        return _estimate_openai_audio_tokens(audio.duration_seconds)
    elif "gemini" in provider_lower or "google" in provider_lower:
        return _estimate_gemini_audio_tokens(audio.duration_seconds)
    else:
        # Default to OpenAI-style estimation
        return _estimate_openai_audio_tokens(audio.duration_seconds)


def analyze_audio_in_messages(
    messages: List[Any],
    provider: str = "openai"
) -> Optional[TokenBreakdown]:
    """
    Analyze messages to count audio clips and estimate token usage.

    Args:
        messages: List of message dicts (OpenAI/LiteLLM format)
        provider: Provider name for token estimation rules

    Returns:
        TokenBreakdown for audio, or None if no audio found

    Audio can appear in messages as:
    - OpenAI: {"type": "input_audio", "input_audio": {"data": "base64...", "format": "wav"}}
    - Generic: {"type": "audio", "audio": {"data": "base64...", "format": "mp3"}}
    """
    audio_clips: List[AudioInfo] = []

    for msg in messages:
        # Handle both dict and object-style messages
        if isinstance(msg, dict):
            content = msg.get("content")
        else:
            content = getattr(msg, "content", None)

        # Skip if content is just a string (no audio)
        if not isinstance(content, list):
            continue

        for part in content:
            if not isinstance(part, dict):
                continue

            part_type = part.get("type", "")

            # OpenAI style: {"type": "input_audio", "input_audio": {...}}
            if part_type == "input_audio":
                audio_obj = part.get("input_audio", {})
                if isinstance(audio_obj, dict):
                    data = audio_obj.get("data", "")
                    audio_format = audio_obj.get("format", "wav")

                    # OpenAI sends raw base64, not data URL
                    if data and not data.startswith("data:"):
                        data = f"data:audio/{audio_format};base64,{data}"

                    duration, detected_format = _get_audio_duration_from_base64(data)
                    audio_clips.append(AudioInfo(
                        duration_seconds=duration,
                        format=audio_format or detected_format,
                        source="base64"
                    ))

            # Generic audio URL style (similar to images)
            elif part_type == "audio_url":
                audio_url_obj = part.get("audio_url", {})
                if isinstance(audio_url_obj, str):
                    url = audio_url_obj
                else:
                    url = audio_url_obj.get("url", "")

                duration = None
                audio_format = "unknown"
                source = "url"

                if url.startswith("data:"):
                    source = "base64"
                    duration, audio_format = _get_audio_duration_from_base64(url)

                audio_clips.append(AudioInfo(
                    duration_seconds=duration,
                    format=audio_format,
                    source=source
                ))

            # Anthropic/generic style: {"type": "audio", "source": {...}}
            elif part_type == "audio":
                source_obj = part.get("source", {})
                if isinstance(source_obj, dict):
                    media_type = source_obj.get("media_type", "audio/wav")
                    data = source_obj.get("data", "")

                    audio_format = media_type.split("/")[-1] if "/" in media_type else "unknown"

                    if data and not data.startswith("data:"):
                        data = f"data:{media_type};base64,{data}"

                    duration, _ = _get_audio_duration_from_base64(data)
                    audio_clips.append(AudioInfo(
                        duration_seconds=duration,
                        format=audio_format,
                        source="base64"
                    ))

    if not audio_clips:
        return None

    # Calculate estimated tokens
    total_tokens = 0
    for clip in audio_clips:
        total_tokens += _estimate_audio_tokens(clip, provider)

    return TokenBreakdown(
        type="audio",
        input_tokens=total_tokens,
        count=len(audio_clips)
    )
