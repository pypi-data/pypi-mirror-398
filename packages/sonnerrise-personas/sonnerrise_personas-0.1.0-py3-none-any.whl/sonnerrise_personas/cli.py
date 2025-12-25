"""Command-line interface for sonnerrise-personas."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sonnerrise_personas import __version__
from sonnerrise_personas.repository import PersonaNotFoundError, PersonaRepository
from sonnerrise_personas.schemas import PersonaCreate, PersonaUpdate


def get_db():
    """Get database connection from config."""
    from sonnerrise_core import get_database, load_config

    config = load_config()
    return get_database(config)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-personas",
        description="Sonnerrise Personas - Manage Suno persona definitions",
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
    list_parser = subparsers.add_parser("list", help="List all personas")
    list_parser.add_argument(
        "-p", "--page", type=int, default=1, help="Page number"
    )
    list_parser.add_argument(
        "-n", "--per-page", type=int, default=20, help="Items per page"
    )
    list_parser.add_argument(
        "-f", "--filter", dest="name_filter", help="Filter by name substring"
    )

    # show command
    show_parser = subparsers.add_parser("show", help="Show persona details")
    show_parser.add_argument("id", type=int, help="Persona ID")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new persona")
    create_parser.add_argument(
        "--name", "-n", required=True, help="Persona name (max 48 chars)"
    )
    create_parser.add_argument(
        "--style", "-s", dest="style_of_music", help="Style of music (max 1000 chars)"
    )
    create_parser.add_argument(
        "--track", "-t", dest="parental_track_id", type=int, help="Parental track ID"
    )
    create_parser.add_argument(
        "--comments", "-C", help="Comments"
    )

    # update command
    update_parser = subparsers.add_parser("update", help="Update a persona")
    update_parser.add_argument("id", type=int, help="Persona ID")
    update_parser.add_argument("--name", "-n", help="New name")
    update_parser.add_argument("--style", "-s", dest="style_of_music", help="New style")
    update_parser.add_argument(
        "--track", "-t", dest="parental_track_id", type=int, help="New parental track ID"
    )
    update_parser.add_argument("--comments", "-C", help="New comments")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a persona")
    delete_parser.add_argument("id", type=int, help="Persona ID")
    delete_parser.add_argument(
        "-f", "--force", action="store_true", help="Skip confirmation"
    )

    # search command
    search_parser = subparsers.add_parser("search", help="Search personas by name")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-l", "--limit", type=int, default=20, help="Maximum results"
    )

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    """List all personas."""
    db = get_db()
    repo = PersonaRepository(db)

    result = repo.list(
        page=args.page,
        per_page=args.per_page,
        name_filter=args.name_filter,
    )

    if not result.items:
        print("No personas found.")
        return 0

    print(f"Personas (page {result.page}/{result.pages}, total: {result.total}):\n")
    print(f"{'ID':<6} {'Name':<30} {'Style':<40}")
    print("-" * 76)

    for persona in result.items:
        style = persona.style_of_music or ""
        if len(style) > 37:
            style = style[:37] + "..."
        print(f"{persona.id:<6} {persona.name:<30} {style:<40}")

    if result.has_next:
        print(f"\nUse --page {result.page + 1} to see more")

    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show persona details."""
    db = get_db()
    repo = PersonaRepository(db)

    try:
        persona = repo.get(args.id)
    except PersonaNotFoundError:
        print(f"Error: Persona {args.id} not found", file=sys.stderr)
        return 1

    print(f"Persona #{persona.id}")
    print(f"  Name: {persona.name}")
    print(f"  Style of Music: {persona.style_of_music or '(none)'}")
    print(f"  Parental Track: {persona.parental_track_id or '(none)'}")
    print(f"  Created: {persona.created_at}")
    print(f"  Updated: {persona.updated_at}")
    if persona.comments:
        print(f"  Comments:\n    {persona.comments}")

    return 0


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new persona."""
    db = get_db()
    db.create_tables()
    repo = PersonaRepository(db)

    try:
        data = PersonaCreate(
            name=args.name,
            style_of_music=args.style_of_music,
            parental_track_id=args.parental_track_id,
            comments=args.comments,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    persona = repo.create(data)
    print(f"Created persona #{persona.id}: {persona.name}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update a persona."""
    db = get_db()
    repo = PersonaRepository(db)

    update_fields = {}
    if args.name is not None:
        update_fields["name"] = args.name
    if args.style_of_music is not None:
        update_fields["style_of_music"] = args.style_of_music
    if args.parental_track_id is not None:
        update_fields["parental_track_id"] = args.parental_track_id
    if args.comments is not None:
        update_fields["comments"] = args.comments

    if not update_fields:
        print("Error: No fields to update", file=sys.stderr)
        return 1

    try:
        data = PersonaUpdate(**update_fields)
        persona = repo.update(args.id, data)
    except PersonaNotFoundError:
        print(f"Error: Persona {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Updated persona #{persona.id}: {persona.name}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a persona."""
    db = get_db()
    repo = PersonaRepository(db)

    if not args.force:
        try:
            persona = repo.get(args.id)
        except PersonaNotFoundError:
            print(f"Error: Persona {args.id} not found", file=sys.stderr)
            return 1

        response = input(f"Delete persona '{persona.name}'? [y/N] ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    if repo.delete(args.id):
        print(f"Deleted persona #{args.id}")
        return 0
    else:
        print(f"Error: Persona {args.id} not found", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search personas by name."""
    db = get_db()
    repo = PersonaRepository(db)

    results = repo.search(args.query, limit=args.limit)

    if not results:
        print(f"No personas found matching '{args.query}'")
        return 0

    print(f"Found {len(results)} persona(s):\n")
    print(f"{'ID':<6} {'Name':<30} {'Style':<40}")
    print("-" * 76)

    for persona in results:
        style = persona.style_of_music or ""
        if len(style) > 37:
            style = style[:37] + "..."
        print(f"{persona.id:<6} {persona.name:<30} {style:<40}")

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
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
