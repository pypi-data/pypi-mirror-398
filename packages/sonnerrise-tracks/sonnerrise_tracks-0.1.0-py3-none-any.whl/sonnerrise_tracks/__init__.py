"""Sonnerrise Tracks - Suno-generated track management module."""

from sonnerrise_tracks.models import Track, TrackEvent, TrackLink
from sonnerrise_tracks.repository import (
    EventNotFoundError,
    TrackNotFoundError,
    TrackRepository,
)
from sonnerrise_tracks.schemas import (
    EventCreate,
    EventRead,
    EventUpdate,
    LinkCreate,
    LinkRead,
    TrackCreate,
    TrackFilter,
    TrackList,
    TrackListItem,
    TrackRead,
    TrackUpdate,
    UpcomingEvent,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Track",
    "TrackEvent",
    "TrackLink",
    # Repository
    "TrackRepository",
    "TrackNotFoundError",
    "EventNotFoundError",
    # Schemas
    "EventCreate",
    "EventRead",
    "EventUpdate",
    "LinkCreate",
    "LinkRead",
    "TrackCreate",
    "TrackFilter",
    "TrackList",
    "TrackListItem",
    "TrackRead",
    "TrackUpdate",
    "UpcomingEvent",
    # Version
    "__version__",
]
