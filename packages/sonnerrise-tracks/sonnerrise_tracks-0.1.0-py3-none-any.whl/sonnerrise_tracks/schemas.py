"""Pydantic schemas for Sonnerrise Tracks."""

from __future__ import annotations

from datetime import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LinkBase(BaseModel):
    """Base schema for track links."""

    url: Annotated[
        str,
        Field(max_length=2048, description="URL"),
    ]
    description: Annotated[
        str | None,
        Field(max_length=120, description="Link description"),
    ] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkCreate(LinkBase):
    """Schema for creating a link."""

    pass


class LinkRead(LinkBase):
    """Schema for reading a link."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class EventBase(BaseModel):
    """Base schema for track events."""

    datetime: Annotated[
        dt,
        Field(description="Event date and time"),
    ]
    description: Annotated[
        str,
        Field(min_length=1, max_length=200, description="Event description"),
    ]
    enabled: Annotated[
        bool,
        Field(description="Whether the event is active"),
    ] = True

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty or whitespace only")
        return v


class EventCreate(EventBase):
    """Schema for creating an event."""

    pass


class EventUpdate(BaseModel):
    """Schema for updating an event."""

    datetime: dt | None = None
    description: Annotated[
        str | None,
        Field(max_length=200, description="Event description"),
    ] = None
    enabled: bool | None = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Ensure description is not just whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Description cannot be empty or whitespace only")
        return v


class EventRead(EventBase):
    """Schema for reading an event."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: int

    @property
    def is_past(self) -> bool:
        """Check if the event is in the past."""
        return self.datetime < dt.now()

    @property
    def is_upcoming(self) -> bool:
        """Check if the event is in the future and enabled."""
        return self.enabled and self.datetime >= dt.now()


class TrackBase(BaseModel):
    """Base schema with common track fields."""

    title: Annotated[
        str,
        Field(min_length=1, max_length=120, description="Track title"),
    ]
    album: Annotated[
        str | None,
        Field(max_length=120, description="Album or playlist name"),
    ] = None
    definition_id: Annotated[
        int | None,
        Field(description="Reference to generation definition"),
    ] = None
    cover_art_url: Annotated[
        str | None,
        Field(max_length=2048, description="Cover art image URL"),
    ] = None
    lyrics: Annotated[
        str | None,
        Field(max_length=32768, description="Track lyrics"),
    ] = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty or whitespace only")
        return v

    @field_validator("cover_art_url")
    @classmethod
    def validate_cover_art_url(cls, v: str | None) -> str | None:
        """Validate cover art URL if provided."""
        if v is not None:
            v = v.strip()
            if v and not v.startswith(("http://", "https://")):
                raise ValueError("Cover art URL must start with http:// or https://")
            return v if v else None
        return v


class TrackCreate(TrackBase):
    """Schema for creating a new track."""

    links: list[LinkCreate] = Field(default_factory=list)
    events: list[EventCreate] = Field(default_factory=list)


class TrackUpdate(BaseModel):
    """Schema for updating an existing track.

    All fields are optional - only provided fields will be updated.
    """

    title: Annotated[
        str | None,
        Field(min_length=1, max_length=120, description="Track title"),
    ] = None
    album: Annotated[
        str | None,
        Field(max_length=120, description="Album or playlist name"),
    ] = None
    definition_id: int | None = None
    cover_art_url: Annotated[
        str | None,
        Field(max_length=2048, description="Cover art image URL"),
    ] = None
    lyrics: Annotated[
        str | None,
        Field(max_length=32768, description="Track lyrics"),
    ] = None
    comments: Annotated[
        str | None,
        Field(max_length=32768, description="Additional comments"),
    ] = None
    links: list[LinkCreate] | None = None
    events: list[EventCreate] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Ensure title is not just whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty or whitespace only")
        return v


class TrackRead(BaseModel):
    """Schema for reading a track from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    album: str | None
    definition_id: int | None
    cover_art_url: str | None
    lyrics: str | None
    comments: str | None
    links: list[LinkRead]
    events: list[EventRead]
    created_at: dt
    updated_at: dt


class TrackListItem(BaseModel):
    """Schema for track list items (abbreviated)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    album: str | None
    definition_id: int | None
    has_cover_art: bool = False
    event_count: int = 0

    @classmethod
    def from_track(cls, track) -> "TrackListItem":
        """Create from a Track model instance."""
        return cls(
            id=track.id,
            title=track.title,
            album=track.album,
            definition_id=track.definition_id,
            has_cover_art=bool(track.cover_art_url),
            event_count=len(track.events) if track.events else 0,
        )


class TrackList(BaseModel):
    """Schema for paginated list of tracks."""

    items: list[TrackListItem]
    total: int
    page: int
    per_page: int
    pages: int

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class TrackFilter(BaseModel):
    """Filter criteria for listing tracks."""

    title: str | None = None
    album: str | None = None
    definition_id: int | None = None
    has_cover_art: bool | None = None
    has_events: bool | None = None


class UpcomingEvent(BaseModel):
    """Schema for upcoming events with track info."""

    model_config = ConfigDict(from_attributes=True)

    event_id: int
    track_id: int
    track_title: str
    datetime: dt
    description: str
    days_until: int

    @classmethod
    def from_event(cls, event, track) -> "UpcomingEvent":
        """Create from event and track model instances."""
        now = dt.now()
        delta = event.datetime - now
        days_until = max(0, delta.days)

        return cls(
            event_id=event.id,
            track_id=track.id,
            track_title=track.title,
            datetime=event.datetime,
            description=event.description,
            days_until=days_until,
        )
