"""Command-line interface for sonnerrise-tracks."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from sonnerrise_tracks import __version__
from sonnerrise_tracks.repository import (
    EventNotFoundError,
    TrackNotFoundError,
    TrackRepository,
)
from sonnerrise_tracks.schemas import (
    EventCreate,
    EventUpdate,
    TrackCreate,
    TrackFilter,
    TrackUpdate,
)


def get_db():
    """Get database connection from config."""
    from sonnerrise_core import get_database, load_config

    config = load_config()
    return get_database(config)


def parse_datetime(s: str) -> datetime:
    """Parse datetime from string."""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {s}. Use YYYY-MM-DD HH:MM")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-tracks",
        description="Sonnerrise Tracks - Manage Suno-generated tracks",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List all tracks")
    list_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    list_parser.add_argument("-n", "--per-page", type=int, default=20, help="Items per page")
    list_parser.add_argument("-t", "--title", help="Filter by title substring")
    list_parser.add_argument("-a", "--album", help="Filter by album substring")
    list_parser.add_argument("-d", "--definition", type=int, help="Filter by definition ID")

    # show command
    show_parser = subparsers.add_parser("show", help="Show track details")
    show_parser.add_argument("id", type=int, help="Track ID")

    # create command
    create_parser_cmd = subparsers.add_parser("create", help="Create a new track")
    create_parser_cmd.add_argument(
        "--title", "-t", required=True, help="Track title (max 120 chars)"
    )
    create_parser_cmd.add_argument("--album", "-a", help="Album or playlist name")
    create_parser_cmd.add_argument("--definition", "-d", type=int, help="Definition ID")
    create_parser_cmd.add_argument("--cover", help="Cover art URL")
    create_parser_cmd.add_argument("--lyrics", "-l", help="Track lyrics")
    create_parser_cmd.add_argument("--comments", "-C", help="Comments")

    # update command
    update_parser = subparsers.add_parser("update", help="Update a track")
    update_parser.add_argument("id", type=int, help="Track ID")
    update_parser.add_argument("--title", "-t", help="New title")
    update_parser.add_argument("--album", "-a", help="New album")
    update_parser.add_argument("--definition", "-d", type=int, help="New definition ID")
    update_parser.add_argument("--cover", help="New cover art URL")
    update_parser.add_argument("--lyrics", "-l", help="New lyrics")
    update_parser.add_argument("--comments", "-C", help="New comments")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a track")
    delete_parser.add_argument("id", type=int, help="Track ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")

    # search command
    search_parser = subparsers.add_parser("search", help="Search tracks")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-l", "--limit", type=int, default=20, help="Maximum results")

    # add-link command
    addlink_parser = subparsers.add_parser("add-link", help="Add a link to a track")
    addlink_parser.add_argument("id", type=int, help="Track ID")
    addlink_parser.add_argument("url", help="URL to add")
    addlink_parser.add_argument("-d", "--description", help="Link description")

    # add-event command
    addevent_parser = subparsers.add_parser("add-event", help="Add an event to a track")
    addevent_parser.add_argument("id", type=int, help="Track ID")
    addevent_parser.add_argument(
        "--datetime", "-D", required=True, help="Event date/time (YYYY-MM-DD HH:MM)"
    )
    addevent_parser.add_argument(
        "--description", "-d", required=True, help="Event description"
    )
    addevent_parser.add_argument(
        "--disabled", action="store_true", help="Create as disabled"
    )

    # events command
    events_parser = subparsers.add_parser("events", help="List upcoming events")
    events_parser.add_argument(
        "--days", "-d", type=int, default=7, help="Days to look ahead"
    )

    # toggle-event command
    toggle_parser = subparsers.add_parser("toggle-event", help="Toggle event enabled status")
    toggle_parser.add_argument("track_id", type=int, help="Track ID")
    toggle_parser.add_argument("event_id", type=int, help="Event ID")

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    """List all tracks."""
    db = get_db()
    repo = TrackRepository(db)

    filters = TrackFilter(
        title=args.title,
        album=args.album,
        definition_id=args.definition,
    )

    result = repo.list(page=args.page, per_page=args.per_page, filters=filters)

    if not result.items:
        print("No tracks found.")
        return 0

    print(f"Tracks (page {result.page}/{result.pages}, total: {result.total}):\n")
    print(f"{'ID':<6} {'Title':<35} {'Album':<25} {'Events':<8}")
    print("-" * 74)

    for item in result.items:
        album = item.album or ""
        if len(album) > 23:
            album = album[:23] + ".."
        print(f"{item.id:<6} {item.title[:33]:<35} {album:<25} {item.event_count:<8}")

    if result.has_next:
        print(f"\nUse --page {result.page + 1} to see more")

    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show track details."""
    db = get_db()
    repo = TrackRepository(db)

    try:
        track = repo.get(args.id)
    except TrackNotFoundError:
        print(f"Error: Track {args.id} not found", file=sys.stderr)
        return 1

    print(f"Track #{track.id}")
    print(f"  Title: {track.title}")
    print(f"  Album: {track.album or '(none)'}")
    print(f"  Definition ID: {track.definition_id or '(none)'}")
    print(f"  Cover Art: {track.cover_art_url or '(none)'}")
    if track.lyrics:
        lyrics_preview = track.lyrics[:100] + "..." if len(track.lyrics) > 100 else track.lyrics
        print(f"  Lyrics: {lyrics_preview}")
    else:
        print("  Lyrics: (none)")
    print(f"  Created: {track.created_at}")
    print(f"  Updated: {track.updated_at}")

    if track.links:
        print("  Links:")
        for link in track.links:
            desc = f" - {link.description}" if link.description else ""
            print(f"    [{link.id}] {link.url}{desc}")

    if track.events:
        print("  Events:")
        for event in track.events:
            status = "enabled" if event.enabled else "DISABLED"
            print(f"    [{event.id}] {event.datetime} - {event.description} ({status})")

    if track.comments:
        print(f"  Comments:\n    {track.comments[:200]}")

    return 0


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new track."""
    db = get_db()
    db.create_tables()
    repo = TrackRepository(db)

    try:
        data = TrackCreate(
            title=args.title,
            album=args.album,
            definition_id=args.definition,
            cover_art_url=args.cover,
            lyrics=args.lyrics,
            comments=args.comments,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    track = repo.create(data)
    print(f"Created track #{track.id}: {track.title}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update a track."""
    db = get_db()
    repo = TrackRepository(db)

    update_fields = {}
    if args.title is not None:
        update_fields["title"] = args.title
    if args.album is not None:
        update_fields["album"] = args.album
    if args.definition is not None:
        update_fields["definition_id"] = args.definition
    if args.cover is not None:
        update_fields["cover_art_url"] = args.cover
    if args.lyrics is not None:
        update_fields["lyrics"] = args.lyrics
    if args.comments is not None:
        update_fields["comments"] = args.comments

    if not update_fields:
        print("Error: No fields to update", file=sys.stderr)
        return 1

    try:
        data = TrackUpdate(**update_fields)
        track = repo.update(args.id, data)
    except TrackNotFoundError:
        print(f"Error: Track {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Updated track #{track.id}: {track.title}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a track."""
    db = get_db()
    repo = TrackRepository(db)

    if not args.force:
        try:
            track = repo.get(args.id)
        except TrackNotFoundError:
            print(f"Error: Track {args.id} not found", file=sys.stderr)
            return 1

        response = input(f"Delete track '{track.title}'? [y/N] ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    if repo.delete(args.id):
        print(f"Deleted track #{args.id}")
        return 0
    else:
        print(f"Error: Track {args.id} not found", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search tracks."""
    db = get_db()
    repo = TrackRepository(db)

    results = repo.search(args.query, limit=args.limit)

    if not results:
        print(f"No tracks found matching '{args.query}'")
        return 0

    print(f"Found {len(results)} track(s):\n")
    print(f"{'ID':<6} {'Title':<35} {'Album':<25}")
    print("-" * 66)

    for track in results:
        album = track.album or ""
        if len(album) > 23:
            album = album[:23] + ".."
        print(f"{track.id:<6} {track.title[:33]:<35} {album:<25}")

    return 0


def cmd_add_link(args: argparse.Namespace) -> int:
    """Add a link to a track."""
    db = get_db()
    repo = TrackRepository(db)

    try:
        track = repo.add_link(args.id, args.url, args.description)
    except TrackNotFoundError:
        print(f"Error: Track {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Added link to track #{track.id}")
    return 0


def cmd_add_event(args: argparse.Namespace) -> int:
    """Add an event to a track."""
    db = get_db()
    repo = TrackRepository(db)

    try:
        event_datetime = parse_datetime(args.datetime)
        data = EventCreate(
            datetime=event_datetime,
            description=args.description,
            enabled=not args.disabled,
        )
        track = repo.add_event(args.id, data)
    except TrackNotFoundError:
        print(f"Error: Track {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Added event to track #{track.id}")
    return 0


def cmd_events(args: argparse.Namespace) -> int:
    """List upcoming events."""
    db = get_db()
    repo = TrackRepository(db)

    events = repo.get_upcoming_events(days=args.days)

    if not events:
        print(f"No upcoming events in the next {args.days} days")
        return 0

    print(f"Upcoming events (next {args.days} days):\n")
    print(f"{'Days':<6} {'Date':<20} {'Track':<25} {'Event':<30}")
    print("-" * 81)

    for event in events:
        date_str = event.datetime.strftime("%Y-%m-%d %H:%M")
        track_title = event.track_title[:23] if len(event.track_title) > 23 else event.track_title
        desc = event.description[:28] if len(event.description) > 28 else event.description
        print(f"{event.days_until:<6} {date_str:<20} {track_title:<25} {desc:<30}")

    return 0


def cmd_toggle_event(args: argparse.Namespace) -> int:
    """Toggle event enabled status."""
    db = get_db()
    repo = TrackRepository(db)

    try:
        track = repo.toggle_event(args.track_id, args.event_id)
    except TrackNotFoundError:
        print(f"Error: Track {args.track_id} not found", file=sys.stderr)
        return 1
    except EventNotFoundError:
        print(f"Error: Event {args.event_id} not found", file=sys.stderr)
        return 1

    # Find the event to show its new status
    event = next((e for e in track.events if e.id == args.event_id), None)
    if event:
        status = "enabled" if event.enabled else "disabled"
        print(f"Event #{args.event_id} is now {status}")

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
        "search": cmd_search,
        "add-link": cmd_add_link,
        "add-event": cmd_add_event,
        "events": cmd_events,
        "toggle-event": cmd_toggle_event,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
