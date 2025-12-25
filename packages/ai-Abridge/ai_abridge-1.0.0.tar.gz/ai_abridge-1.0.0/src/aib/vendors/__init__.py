"""Vendor adapters package."""

from .base import VendorAdapter
from .gemini import GeminiAdapter
from .kimi import KimiAdapter
from .qwen import QwenAdapter
from .openai import OpenAIAdapter

__all__ = [
    "VendorAdapter",
    "GeminiAdapter",
    "KimiAdapter",
    "QwenAdapter",
    "OpenAIAdapter",
]


def get_adapter(vendor: str, **kwargs) -> VendorAdapter:
    """
    Factory function to get vendor adapter.
    
    Args:
        vendor: Vendor name (gemini, kimi, qwen, openai).
        **kwargs: Adapter configuration (api_key, model, base_url).
    
    Returns:
        Configured VendorAdapter instance.
    
    Raises:
        ValueError: If vendor is not supported.
    """
    vendor = vendor.lower().strip()
    
    adapters = {
        "gemini": GeminiAdapter,
        "kimi": KimiAdapter,
        "qwen": QwenAdapter,
        "openai": OpenAIAdapter,
    }
    
    if vendor not in adapters:
        raise ValueError(f"Unsupported vendor: {vendor}. Supported: {list(adapters.keys())}")
    
    return adapters[vendor](**kwargs)
