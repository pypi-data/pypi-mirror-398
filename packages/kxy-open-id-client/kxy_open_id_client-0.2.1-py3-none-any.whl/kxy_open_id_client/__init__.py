"""
kxy-open-id-client - Client library for KXY Open ID Service
"""

from .client import (
    SegmentClient,
    IdGenerator,
    AsyncIdGenerator,
    IdGeneratorFactory,
    AsyncIdGeneratorFactory,
)
from .models import SegmentRequest, SegmentResponse, ApiResponse
from .exceptions import OpenIdClientError, OpenIdAPIError

__version__ = "0.1.0"
__all__ = [
    "SegmentClient",
    "IdGenerator",
    "AsyncIdGenerator",
    "IdGeneratorFactory",
    "AsyncIdGeneratorFactory",
    "SegmentRequest",
    "SegmentResponse",
    "ApiResponse",
    "OpenIdClientError",
    "OpenIdAPIError",
]
