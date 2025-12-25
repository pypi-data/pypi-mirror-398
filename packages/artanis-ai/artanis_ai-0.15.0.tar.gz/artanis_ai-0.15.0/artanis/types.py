"""Type definitions for Artanis SDK."""

from typing import Any, Callable, Dict, Literal, Optional, Union
from typing_extensions import TypedDict


class ArtanisConfig(TypedDict, total=False):
    """Configuration options for Artanis client."""

    api_key: str
    base_url: str
    enabled: bool
    debug: bool
    on_error: Optional[Callable[[Exception], None]]


# Observation type enumeration
ObservationType = Literal["input", "output", "state"]


class TraceData(TypedDict, total=False):
    """Internal trace data structure."""

    trace_id: str
    name: str
    metadata: Optional[Dict[str, Any]]
    timestamp: str
    status: Optional[Literal["running", "completed"]]
    duration_ms: Optional[int]


class ObservationData(TypedDict, total=False):
    """Observation data structure."""

    trace_id: str
    type: ObservationType
    data: Any
    key: Optional[str]
    timestamp: str


class FeedbackData(TypedDict, total=False):
    """Feedback data structure."""

    trace_id: str
    rating: Union[str, float]
    comment: Optional[str]
    correction: Optional[Dict[str, Any]]
    timestamp: str


# Type aliases
Rating = Union[str, float]
Metadata = Dict[str, Any]
