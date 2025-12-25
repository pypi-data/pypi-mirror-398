"""SQLAlchemy models for Sonnerrise Tracks."""

from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sonnerrise_core.models import BaseModel

if TYPE_CHECKING:
    from sonnerrise_definitions.models import Definition


class Track(BaseModel):
    """Suno-generated track.

    Represents a track that was generated using a Definition,
    with associated metadata, events, and links.
    """

    __tablename__ = "tracks"

    # Basic info
    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )
    album: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    # Reference to generation definition
    definition_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("definitions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Media
    cover_art_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    lyrics: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Comments
    comments: Mapped[str | None] = mapped_column(
        Text(length=32768),
        nullable=True,
    )

    # Relationships
    links: Mapped[list["TrackLink"]] = relationship(
        "TrackLink",
        back_populates="track",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events: Mapped[list["TrackEvent"]] = relationship(
        "TrackEvent",
        back_populates="track",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TrackEvent.datetime",
    )

    # These will be available when respective modules are loaded
    # definition = relationship("Definition", back_populates="tracks")

    def __repr__(self) -> str:
        return f"<Track(id={self.id}, title='{self.title}')>"


class TrackLink(BaseModel):
    """URL link associated with a track."""

    __tablename__ = "track_links"

    track_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Relationship
    track: Mapped[Track] = relationship(
        "Track",
        back_populates="links",
    )

    def __repr__(self) -> str:
        return f"<TrackLink(id={self.id}, url='{self.url[:50]}...')>"


class TrackEvent(BaseModel):
    """Scheduled event for a track.

    Events are used to track publication dates, promotional activities,
    and other time-based milestones for a track.
    """

    __tablename__ = "track_events"

    track_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    datetime: Mapped[dt] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationship
    track: Mapped[Track] = relationship(
        "Track",
        back_populates="events",
    )

    @property
    def is_past(self) -> bool:
        """Check if the event is in the past."""
        return self.datetime < dt.now()

    @property
    def is_upcoming(self) -> bool:
        """Check if the event is in the future and enabled."""
        return self.enabled and self.datetime >= dt.now()

    def __repr__(self) -> str:
        return f"<TrackEvent(id={self.id}, datetime={self.datetime}, description='{self.description[:30]}')>"
