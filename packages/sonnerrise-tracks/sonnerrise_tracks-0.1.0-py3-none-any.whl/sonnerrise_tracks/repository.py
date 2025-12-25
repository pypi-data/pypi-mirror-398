"""Repository layer for Sonnerrise Tracks."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import and_, func

from sonnerrise_tracks.models import Track, TrackEvent, TrackLink
from sonnerrise_tracks.schemas import (
    EventCreate,
    EventRead,
    EventUpdate,
    TrackCreate,
    TrackFilter,
    TrackList,
    TrackListItem,
    TrackRead,
    TrackUpdate,
    UpcomingEvent,
)

if TYPE_CHECKING:
    from sonnerrise_core.database import DatabasePlugin


class TrackNotFoundError(Exception):
    """Raised when a track is not found."""

    def __init__(self, track_id: int) -> None:
        self.track_id = track_id
        super().__init__(f"Track with id {track_id} not found")


class EventNotFoundError(Exception):
    """Raised when an event is not found."""

    def __init__(self, event_id: int) -> None:
        self.event_id = event_id
        super().__init__(f"Event with id {event_id} not found")


class TrackRepository:
    """Repository for managing Track entities.

    Provides CRUD operations, filtering, search, and event management.
    """

    def __init__(self, db: DatabasePlugin) -> None:
        """Initialize the repository.

        Args:
            db: Database plugin instance.
        """
        self._db = db

    def create(self, data: TrackCreate) -> TrackRead:
        """Create a new track.

        Args:
            data: Track creation data.

        Returns:
            The created track.
        """
        with self._db.session() as session:
            track = Track(
                title=data.title,
                album=data.album,
                definition_id=data.definition_id,
                cover_art_url=data.cover_art_url,
                lyrics=data.lyrics,
                comments=data.comments,
            )
            session.add(track)
            session.flush()

            # Add links
            for link_data in data.links:
                link = TrackLink(
                    track_id=track.id,
                    url=link_data.url,
                    description=link_data.description,
                )
                session.add(link)

            # Add events
            for event_data in data.events:
                event = TrackEvent(
                    track_id=track.id,
                    datetime=event_data.datetime,
                    description=event_data.description,
                    enabled=event_data.enabled,
                )
                session.add(event)

            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def get(self, track_id: int) -> TrackRead:
        """Get a track by ID.

        Args:
            track_id: The track ID.

        Returns:
            The track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)
            return TrackRead.model_validate(track)

    def get_or_none(self, track_id: int) -> TrackRead | None:
        """Get a track by ID, returning None if not found.

        Args:
            track_id: The track ID.

        Returns:
            The track or None.
        """
        try:
            return self.get(track_id)
        except TrackNotFoundError:
            return None

    def update(self, track_id: int, data: TrackUpdate) -> TrackRead:
        """Update an existing track.

        Args:
            track_id: The track ID.
            data: Update data (only non-None fields are updated).

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            update_data = data.model_dump(exclude_unset=True, exclude={"links", "events"})
            for field, value in update_data.items():
                setattr(track, field, value)

            # Update links if provided
            if data.links is not None:
                for link in track.links:
                    session.delete(link)
                for link_data in data.links:
                    link = TrackLink(
                        track_id=track.id,
                        url=link_data.url,
                        description=link_data.description,
                    )
                    session.add(link)

            # Update events if provided
            if data.events is not None:
                for event in track.events:
                    session.delete(event)
                for event_data in data.events:
                    event = TrackEvent(
                        track_id=track.id,
                        datetime=event_data.datetime,
                        description=event_data.description,
                        enabled=event_data.enabled,
                    )
                    session.add(event)

            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def delete(self, track_id: int) -> bool:
        """Delete a track.

        Args:
            track_id: The track ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                return False
            session.delete(track)
            session.commit()
            return True

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: TrackFilter | None = None,
    ) -> TrackList:
        """List tracks with pagination and filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            filters: Optional filter criteria.

        Returns:
            Paginated list of tracks.
        """
        with self._db.session() as session:
            query = session.query(Track)

            # Apply filters
            if filters:
                if filters.title:
                    query = query.filter(Track.title.ilike(f"%{filters.title}%"))
                if filters.album:
                    query = query.filter(Track.album.ilike(f"%{filters.album}%"))
                if filters.definition_id is not None:
                    query = query.filter(Track.definition_id == filters.definition_id)
                if filters.has_cover_art is not None:
                    if filters.has_cover_art:
                        query = query.filter(Track.cover_art_url.isnot(None))
                    else:
                        query = query.filter(Track.cover_art_url.is_(None))
                if filters.has_events is not None:
                    if filters.has_events:
                        query = query.filter(Track.events.any())
                    else:
                        query = query.filter(~Track.events.any())

            # Get total count
            total = query.count()

            # Calculate pagination
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            offset = (page - 1) * per_page

            # Get items
            tracks = (
                query.order_by(Track.title)
                .offset(offset)
                .limit(per_page)
                .all()
            )

            return TrackList(
                items=[TrackListItem.from_track(t) for t in tracks],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
            )

    def search(self, query: str, limit: int = 20) -> list[TrackRead]:
        """Search tracks by title or album.

        Args:
            query: Search query (substring match).
            limit: Maximum results to return.

        Returns:
            List of matching tracks.
        """
        with self._db.session() as session:
            tracks = (
                session.query(Track)
                .filter(
                    (Track.title.ilike(f"%{query}%"))
                    | (Track.album.ilike(f"%{query}%"))
                )
                .order_by(Track.title)
                .limit(limit)
                .all()
            )
            return [TrackRead.model_validate(t) for t in tracks]

    def count(self) -> int:
        """Get total count of tracks.

        Returns:
            Total number of tracks.
        """
        with self._db.session() as session:
            return session.query(func.count(Track.id)).scalar() or 0

    def exists(self, track_id: int) -> bool:
        """Check if a track exists.

        Args:
            track_id: The track ID.

        Returns:
            True if exists, False otherwise.
        """
        with self._db.session() as session:
            return (
                session.query(Track.id)
                .filter(Track.id == track_id)
                .first()
                is not None
            )

    def get_by_definition(self, definition_id: int) -> list[TrackRead]:
        """Get all tracks created from a specific definition.

        Args:
            definition_id: The definition ID.

        Returns:
            List of tracks using this definition.
        """
        with self._db.session() as session:
            tracks = (
                session.query(Track)
                .filter(Track.definition_id == definition_id)
                .order_by(Track.title)
                .all()
            )
            return [TrackRead.model_validate(t) for t in tracks]

    # Link management

    def add_link(
        self,
        track_id: int,
        url: str,
        description: str | None = None,
    ) -> TrackRead:
        """Add a link to a track.

        Args:
            track_id: The track ID.
            url: The URL to add.
            description: Optional description.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            link = TrackLink(
                track_id=track_id,
                url=url,
                description=description,
            )
            session.add(link)
            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def remove_link(self, track_id: int, link_id: int) -> TrackRead:
        """Remove a link from a track.

        Args:
            track_id: The track ID.
            link_id: The link ID to remove.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            link = (
                session.query(TrackLink)
                .filter(
                    TrackLink.id == link_id,
                    TrackLink.track_id == track_id,
                )
                .first()
            )
            if link:
                session.delete(link)

            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    # Event management

    def add_event(self, track_id: int, data: EventCreate) -> TrackRead:
        """Add an event to a track.

        Args:
            track_id: The track ID.
            data: Event creation data.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            event = TrackEvent(
                track_id=track_id,
                datetime=data.datetime,
                description=data.description,
                enabled=data.enabled,
            )
            session.add(event)
            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def update_event(
        self,
        track_id: int,
        event_id: int,
        data: EventUpdate,
    ) -> TrackRead:
        """Update an event.

        Args:
            track_id: The track ID.
            event_id: The event ID.
            data: Update data.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
            EventNotFoundError: If event not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            event = (
                session.query(TrackEvent)
                .filter(
                    TrackEvent.id == event_id,
                    TrackEvent.track_id == track_id,
                )
                .first()
            )
            if event is None:
                raise EventNotFoundError(event_id)

            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(event, field, value)

            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def remove_event(self, track_id: int, event_id: int) -> TrackRead:
        """Remove an event from a track.

        Args:
            track_id: The track ID.
            event_id: The event ID to remove.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            event = (
                session.query(TrackEvent)
                .filter(
                    TrackEvent.id == event_id,
                    TrackEvent.track_id == track_id,
                )
                .first()
            )
            if event:
                session.delete(event)

            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def toggle_event(self, track_id: int, event_id: int) -> TrackRead:
        """Toggle an event's enabled status.

        Args:
            track_id: The track ID.
            event_id: The event ID.

        Returns:
            The updated track.

        Raises:
            TrackNotFoundError: If track not found.
            EventNotFoundError: If event not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            event = (
                session.query(TrackEvent)
                .filter(
                    TrackEvent.id == event_id,
                    TrackEvent.track_id == track_id,
                )
                .first()
            )
            if event is None:
                raise EventNotFoundError(event_id)

            event.enabled = not event.enabled
            session.commit()
            session.refresh(track)
            return TrackRead.model_validate(track)

    def get_upcoming_events(self, days: int = 7) -> list[UpcomingEvent]:
        """Get all upcoming events within a time range.

        Args:
            days: Number of days to look ahead.

        Returns:
            List of upcoming events with track info.
        """
        with self._db.session() as session:
            now = datetime.now()
            end_date = now + timedelta(days=days)

            events = (
                session.query(TrackEvent)
                .join(Track)
                .filter(
                    and_(
                        TrackEvent.enabled == True,
                        TrackEvent.datetime >= now,
                        TrackEvent.datetime <= end_date,
                    )
                )
                .order_by(TrackEvent.datetime)
                .all()
            )

            return [
                UpcomingEvent.from_event(e, e.track)
                for e in events
            ]

    def get_all_events(self, track_id: int) -> list[EventRead]:
        """Get all events for a track.

        Args:
            track_id: The track ID.

        Returns:
            List of events.

        Raises:
            TrackNotFoundError: If track not found.
        """
        with self._db.session() as session:
            track = session.query(Track).get(track_id)
            if track is None:
                raise TrackNotFoundError(track_id)

            return [EventRead.model_validate(e) for e in track.events]
