from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)
class ModelPrice:
    input_per_million: float
    output_per_million: float


@dataclass(frozen=True)
class ImageGenerationPrice:
    """Pricing for image generation models (per-image pricing)."""
    # Price per image by size and quality
    # Key format: "size" or "size:quality" (e.g., "1024x1024", "1024x1024:hd")
    prices: dict[str, float]

    def get_price(self, size: str = "1024x1024", quality: str = "standard") -> Optional[float]:
        """Get price for a specific size and quality combination."""
        # Try size:quality first
        key = f"{size}:{quality}"
        if key in self.prices:
            return self.prices[key]
        # Fall back to just size
        if size in self.prices:
            return self.prices[size]
        # Fall back to default
        if "default" in self.prices:
            return self.prices["default"]
        return None


@dataclass(frozen=True)
class ModelKey:
    provider: str
    model: str

_DATE_SUFFIX = re.compile(r"-\d{4}-\d{2}-\d{2}$")

def canonicalize(provider: str, model: str) -> ModelKey:
    p = provider.strip().lower()

    m = model.strip()
    # ensure "openai/..." prefix is present if that's your convention
    if "/" not in m:
        m = f"{p}/{m}"

    # strip dated suffix: openai/gpt-4.1-2025-04-14 -> openai/gpt-4.1
    m = _DATE_SUFFIX.sub("", m)

    return ModelKey(provider=p, model=m)


class PricingRegistry:
    def __init__(self):
        self._prices: dict[ModelKey, ModelPrice] = {}
        self._image_gen_prices: dict[ModelKey, ImageGenerationPrice] = {}

    def set_price(self, provider: str, model: str, *, input_per_million: float, output_per_million: float) -> None:
        key = canonicalize(provider, model)
        self._prices[key] = ModelPrice(
            input_per_million=float(input_per_million),
            output_per_million=float(output_per_million),
        )

    def get_price(self, provider: str, model: str) -> ModelPrice:
        key = canonicalize(provider, model)
        try:
            return self._prices[key]
        except KeyError as e:
            raise KeyError(f"No pricing configured for {key.provider}/{key.model}") from e

    def set_image_generation_price(
        self,
        provider: str,
        model: str,
        *,
        prices: dict[str, float],
    ) -> None:
        """
        Set per-image pricing for an image generation model.

        Args:
            provider: Provider name (e.g., "openai")
            model: Model name (e.g., "dall-e-3")
            prices: Dict mapping size/quality to price per image.
                    Keys can be:
                    - "1024x1024" (size only)
                    - "1024x1024:standard" (size:quality)
                    - "1024x1024:hd" (size:quality)
                    - "default" (fallback price)

        Example:
            pricing.set_image_generation_price(
                provider="openai",
                model="dall-e-3",
                prices={
                    "1024x1024:standard": 0.040,
                    "1024x1024:hd": 0.080,
                    "1792x1024:standard": 0.080,
                    "1792x1024:hd": 0.120,
                    "default": 0.040,
                }
            )
        """
        key = canonicalize(provider, model)
        self._image_gen_prices[key] = ImageGenerationPrice(prices=prices)

    def get_image_generation_price(self, provider: str, model: str) -> Optional[ImageGenerationPrice]:
        """Get image generation pricing for a model, or None if not configured."""
        key = canonicalize(provider, model)
        return self._image_gen_prices.get(key)