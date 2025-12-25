"""Command-line interface for sonnerrise-promo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sonnerrise_promo import __version__
from sonnerrise_promo.repository import (
    PromoExistsError,
    PromoNotFoundError,
    PromoRepository,
)
from sonnerrise_promo.schemas import PromoCreate, PromoFilter, PromoUpdate


def get_db():
    """Get database connection from config."""
    from sonnerrise_core import get_database, load_config

    config = load_config()
    return get_database(config)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-promo",
        description="Sonnerrise Promo - Manage track promotion materials",
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
    list_parser = subparsers.add_parser("list", help="List all promos")
    list_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    list_parser.add_argument("-n", "--per-page", type=int, default=20, help="Items per page")
    list_parser.add_argument("-t", "--track", type=int, help="Filter by track ID")
    list_parser.add_argument("--has-art", action="store_true", help="Only with art definition")
    list_parser.add_argument("--has-pitch", action="store_true", help="Only with pitch")

    # show command
    show_parser = subparsers.add_parser("show", help="Show promo details")
    show_parser.add_argument("id", type=int, help="Promo ID")

    # show-track command
    show_track_parser = subparsers.add_parser("show-track", help="Show promo for a track")
    show_track_parser.add_argument("track_id", type=int, help="Track ID")

    # create command
    create_parser_cmd = subparsers.add_parser("create", help="Create a new promo")
    create_parser_cmd.add_argument(
        "--track", "-t", type=int, required=True, help="Track ID"
    )
    create_parser_cmd.add_argument("--art", help="Track art definition (AI prompt)")
    create_parser_cmd.add_argument("--canvas", help="Track canvas definition (AI prompt)")
    create_parser_cmd.add_argument("--pitch", "-p", help="Marketing pitch/blurb")

    # update command
    update_parser = subparsers.add_parser("update", help="Update a promo")
    update_parser.add_argument("id", type=int, help="Promo ID")
    update_parser.add_argument("--art", help="New track art definition")
    update_parser.add_argument("--canvas", help="New track canvas definition")
    update_parser.add_argument("--pitch", "-p", help="New pitch")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a promo")
    delete_parser.add_argument("id", type=int, help="Promo ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")

    # add-link command
    addlink_parser = subparsers.add_parser("add-link", help="Add a link to a promo")
    addlink_parser.add_argument("id", type=int, help="Promo ID")
    addlink_parser.add_argument("--url", "-u", required=True, help="URL to add")
    addlink_parser.add_argument("-d", "--description", help="Link description")

    # remove-link command
    rmlink_parser = subparsers.add_parser("remove-link", help="Remove a link from a promo")
    rmlink_parser.add_argument("promo_id", type=int, help="Promo ID")
    rmlink_parser.add_argument("link_id", type=int, help="Link ID")

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    """List all promos."""
    db = get_db()
    repo = PromoRepository(db)

    filters = PromoFilter(
        track_id=args.track,
        has_art_definition=True if args.has_art else None,
        has_pitch=True if args.has_pitch else None,
    )

    result = repo.list(page=args.page, per_page=args.per_page, filters=filters)

    if not result.items:
        print("No promos found.")
        return 0

    print(f"Promos (page {result.page}/{result.pages}, total: {result.total}):\n")
    print(f"{'ID':<6} {'Track':<8} {'Art':<6} {'Canvas':<8} {'Pitch':<7} {'Links':<6}")
    print("-" * 41)

    for item in result.items:
        art = "Yes" if item.has_art_definition else "-"
        canvas = "Yes" if item.has_canvas_definition else "-"
        pitch = "Yes" if item.has_pitch else "-"
        print(
            f"{item.id:<6} {item.track_id:<8} {art:<6} {canvas:<8} {pitch:<7} {item.link_count:<6}"
        )

    if result.has_next:
        print(f"\nUse --page {result.page + 1} to see more")

    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show promo details."""
    db = get_db()
    repo = PromoRepository(db)

    try:
        promo = repo.get(args.id)
    except PromoNotFoundError:
        print(f"Error: Promo {args.id} not found", file=sys.stderr)
        return 1

    _display_promo(promo)
    return 0


def cmd_show_track(args: argparse.Namespace) -> int:
    """Show promo for a track."""
    db = get_db()
    repo = PromoRepository(db)

    promo = repo.get_by_track(args.track_id)
    if promo is None:
        print(f"No promo found for track {args.track_id}")
        return 0

    _display_promo(promo)
    return 0


def _display_promo(promo) -> None:
    """Display promo details."""
    print(f"Promo #{promo.id}")
    print(f"  Track ID: {promo.track_id}")
    print(f"  Created: {promo.created_at}")
    print(f"  Updated: {promo.updated_at}")

    if promo.track_art_definition:
        art_preview = promo.track_art_definition[:200]
        if len(promo.track_art_definition) > 200:
            art_preview += "..."
        print(f"\n  Track Art Definition:\n    {art_preview}")
    else:
        print("\n  Track Art Definition: (none)")

    if promo.track_canvas_definition:
        canvas_preview = promo.track_canvas_definition[:200]
        if len(promo.track_canvas_definition) > 200:
            canvas_preview += "..."
        print(f"\n  Track Canvas Definition:\n    {canvas_preview}")
    else:
        print("\n  Track Canvas Definition: (none)")

    if promo.pitch:
        pitch_preview = promo.pitch[:300]
        if len(promo.pitch) > 300:
            pitch_preview += "..."
        print(f"\n  Pitch:\n    {pitch_preview}")
    else:
        print("\n  Pitch: (none)")

    if promo.links:
        print("\n  Links:")
        for link in promo.links:
            desc = f" - {link.description}" if link.description else ""
            print(f"    [{link.id}] {link.url}{desc}")


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new promo."""
    db = get_db()
    db.create_tables()
    repo = PromoRepository(db)

    try:
        data = PromoCreate(
            track_id=args.track,
            track_art_definition=args.art,
            track_canvas_definition=args.canvas,
            pitch=args.pitch,
        )
        promo = repo.create(data)
    except PromoExistsError:
        print(f"Error: Promo already exists for track {args.track}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Created promo #{promo.id} for track {promo.track_id}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update a promo."""
    db = get_db()
    repo = PromoRepository(db)

    update_fields = {}
    if args.art is not None:
        update_fields["track_art_definition"] = args.art
    if args.canvas is not None:
        update_fields["track_canvas_definition"] = args.canvas
    if args.pitch is not None:
        update_fields["pitch"] = args.pitch

    if not update_fields:
        print("Error: No fields to update", file=sys.stderr)
        return 1

    try:
        data = PromoUpdate(**update_fields)
        promo = repo.update(args.id, data)
    except PromoNotFoundError:
        print(f"Error: Promo {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Updated promo #{promo.id}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a promo."""
    db = get_db()
    repo = PromoRepository(db)

    if not args.force:
        try:
            promo = repo.get(args.id)
        except PromoNotFoundError:
            print(f"Error: Promo {args.id} not found", file=sys.stderr)
            return 1

        response = input(f"Delete promo for track {promo.track_id}? [y/N] ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    if repo.delete(args.id):
        print(f"Deleted promo #{args.id}")
        return 0
    else:
        print(f"Error: Promo {args.id} not found", file=sys.stderr)
        return 1


def cmd_add_link(args: argparse.Namespace) -> int:
    """Add a link to a promo."""
    db = get_db()
    repo = PromoRepository(db)

    try:
        promo = repo.add_link(args.id, args.url, args.description)
    except PromoNotFoundError:
        print(f"Error: Promo {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Added link to promo #{promo.id}")
    return 0


def cmd_remove_link(args: argparse.Namespace) -> int:
    """Remove a link from a promo."""
    db = get_db()
    repo = PromoRepository(db)

    try:
        promo = repo.remove_link(args.promo_id, args.link_id)
    except PromoNotFoundError:
        print(f"Error: Promo {args.promo_id} not found", file=sys.stderr)
        return 1

    print(f"Removed link from promo #{promo.id}")
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
        "show-track": cmd_show_track,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
        "add-link": cmd_add_link,
        "remove-link": cmd_remove_link,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
