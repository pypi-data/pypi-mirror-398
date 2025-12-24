"""
Oximy Python SDK

Zero-overhead observability for LLM applications.
"""

from .client import Oximy, create_oximy
from .types import (
    OximyConfig,
    RequestContext,
    OximyEvent,
    EventSource,
    EventTiming,
    EventOutcome,
    EventContext,
    StreamingInfo,
    NormalizedData,
    ProjectSettings,
    PolicyMode,
    PolicyConfig,
    PolicyRule,
    PolicyViolation,
    OximyError,
    OximyPolicyError,
    Provider,
    EventType,
)

__version__ = "0.0.2"

__all__ = [
    "Oximy",
    "create_oximy",
    "OximyConfig",
    "RequestContext",
    "OximyEvent",
    "EventSource",
    "EventTiming",
    "EventOutcome",
    "EventContext",
    "StreamingInfo",
    "NormalizedData",
    "ProjectSettings",
    "PolicyMode",
    "PolicyConfig",
    "PolicyRule",
    "PolicyViolation",
    "OximyError",
    "OximyPolicyError",
    "Provider",
    "EventType",
]
