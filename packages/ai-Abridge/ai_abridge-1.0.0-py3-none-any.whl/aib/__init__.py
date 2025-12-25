"""
AI Bridge - A pure AI model bridge.

Transparent, native SDK, multi-vendor support.
"""

from .bridge import AIBridge
from .models import Response, VendorType

__all__ = ["AIBridge", "Response", "VendorType"]
__version__ = "3.0.0"
