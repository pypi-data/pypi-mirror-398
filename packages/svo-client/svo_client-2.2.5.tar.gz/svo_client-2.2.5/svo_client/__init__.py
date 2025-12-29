"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SVO Client - Async client for SVO semantic chunker microservice.
"""

from svo_client.chunker_client import ChunkerClient
from svo_client.errors import (
    SVOChunkingIntegrityError,
    SVOConnectionError,
    SVOEmbeddingError,
    SVOHTTPError,
    SVOJSONRPCError,
    SVOServerError,
    SVOTimeoutError,
)
from svo_client.config_tools import ConfigGenerator, ConfigValidator

__all__ = [
    "ChunkerClient",
    "SVOServerError",
    "SVOJSONRPCError",
    "SVOHTTPError",
    "SVOConnectionError",
    "SVOTimeoutError",
    "SVOEmbeddingError",
    "SVOChunkingIntegrityError",
    "ConfigGenerator",
    "ConfigValidator",
]

__version__ = "2.2.5"
