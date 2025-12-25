"""Command-line interface for sonnerrise-definitions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sonnerrise_definitions import __version__
from sonnerrise_definitions.models import ModelVersion, PersonaType, ServiceType, VocalsType
from sonnerrise_definitions.repository import DefinitionNotFoundError, DefinitionRepository
from sonnerrise_definitions.schemas import DefinitionCreate, DefinitionFilter, DefinitionUpdate


def get_db():
    """Get database connection from config."""
    from sonnerrise_core import get_database, load_config

    config = load_config()
    return get_database(config)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-definitions",
        description="Sonnerrise Definitions - Manage Suno generation definitions",
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
    list_parser = subparsers.add_parser("list", help="List all definitions")
    list_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    list_parser.add_argument("-n", "--per-page", type=int, default=20, help="Items per page")
    list_parser.add_argument("-t", "--title", help="Filter by title substring")
    list_parser.add_argument(
        "-m", "--model",
        choices=[m.value for m in ModelVersion],
        help="Filter by model version",
    )
    list_parser.add_argument(
        "-v", "--vocals",
        choices=[v.value for v in VocalsType],
        help="Filter by vocals type",
    )

    # show command
    show_parser = subparsers.add_parser("show", help="Show definition details")
    show_parser.add_argument("id", type=int, help="Definition ID")

    # create command
    create_parser_cmd = subparsers.add_parser("create", help="Create a new definition")
    create_parser_cmd.add_argument(
        "--title", "-t", required=True, help="Definition title (max 120 chars)"
    )
    create_parser_cmd.add_argument("--annotation", "-a", help="Short annotation (max 200 chars)")
    create_parser_cmd.add_argument(
        "--model", "-m",
        choices=[m.value for m in ModelVersion],
        default=ModelVersion.V4_0.value,
        help="Model version",
    )
    create_parser_cmd.add_argument("--style", "-s", help="Style of music (max 1000 chars)")
    create_parser_cmd.add_argument("--lyrics", "-l", help="Song lyrics (max 3000 chars)")
    create_parser_cmd.add_argument("--persona", type=int, help="Persona ID")
    create_parser_cmd.add_argument(
        "--persona-type",
        choices=[p.value for p in PersonaType],
        help="Persona type (voice or style)",
    )
    create_parser_cmd.add_argument(
        "--vocals", "-v",
        choices=[v.value for v in VocalsType],
        default=VocalsType.ANY.value,
        help="Vocals type",
    )
    create_parser_cmd.add_argument(
        "--audio-influence", type=int, default=25, help="Audio influence (0-100)"
    )
    create_parser_cmd.add_argument(
        "--style-influence", type=int, default=50, help="Style influence (0-100)"
    )
    create_parser_cmd.add_argument("--weirdness", type=int, default=50, help="Weirdness (0-100)")
    create_parser_cmd.add_argument("--comments", "-C", help="Comments")

    # update command
    update_parser = subparsers.add_parser("update", help="Update a definition")
    update_parser.add_argument("id", type=int, help="Definition ID")
    update_parser.add_argument("--title", "-t", help="New title")
    update_parser.add_argument("--annotation", "-a", help="New annotation")
    update_parser.add_argument(
        "--model", "-m",
        choices=[m.value for m in ModelVersion],
        help="New model version",
    )
    update_parser.add_argument("--style", "-s", help="New style of music")
    update_parser.add_argument("--lyrics", "-l", help="New lyrics")
    update_parser.add_argument(
        "--vocals", "-v",
        choices=[v.value for v in VocalsType],
        help="New vocals type",
    )
    update_parser.add_argument("--audio-influence", type=int, help="New audio influence")
    update_parser.add_argument("--style-influence", type=int, help="New style influence")
    update_parser.add_argument("--weirdness", type=int, help="New weirdness")
    update_parser.add_argument("--comments", "-C", help="New comments")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a definition")
    delete_parser.add_argument("id", type=int, help="Definition ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")

    # search command
    search_parser = subparsers.add_parser("search", help="Search definitions")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-l", "--limit", type=int, default=20, help="Maximum results")

    # add-link command
    addlink_parser = subparsers.add_parser("add-link", help="Add a link to a definition")
    addlink_parser.add_argument("id", type=int, help="Definition ID")
    addlink_parser.add_argument("url", help="URL to add")
    addlink_parser.add_argument("-d", "--description", help="Link description")

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    """List all definitions."""
    db = get_db()
    repo = DefinitionRepository(db)

    filters = DefinitionFilter(
        title=args.title,
        model=ModelVersion(args.model) if args.model else None,
        vocals=VocalsType(args.vocals) if args.vocals else None,
    )

    result = repo.list(page=args.page, per_page=args.per_page, filters=filters)

    if not result.items:
        print("No definitions found.")
        return 0

    print(f"Definitions (page {result.page}/{result.pages}, total: {result.total}):\n")
    print(f"{'ID':<6} {'Title':<35} {'Model':<8} {'Style':<30}")
    print("-" * 79)

    for item in result.items:
        style = item.style_snippet or ""
        print(f"{item.id:<6} {item.title[:33]:<35} {item.model.value:<8} {style:<30}")

    if result.has_next:
        print(f"\nUse --page {result.page + 1} to see more")

    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show definition details."""
    db = get_db()
    repo = DefinitionRepository(db)

    try:
        definition = repo.get(args.id)
    except DefinitionNotFoundError:
        print(f"Error: Definition {args.id} not found", file=sys.stderr)
        return 1

    print(f"Definition #{definition.id}")
    print(f"  Title: {definition.title}")
    print(f"  Annotation: {definition.annotation or '(none)'}")
    print(f"  Service: {definition.service.value}")
    print(f"  Model: {definition.model.value}")
    print(f"  Vocals: {definition.vocals.value}")
    print(f"  Style of Music: {definition.style_of_music or '(none)'}")
    if definition.lyrics:
        lyrics_preview = definition.lyrics[:100] + "..." if len(definition.lyrics) > 100 else definition.lyrics
        print(f"  Lyrics: {lyrics_preview}")
    else:
        print("  Lyrics: (none)")
    print(f"  Persona ID: {definition.persona_id or '(none)'}")
    if definition.persona_id:
        print(f"  Persona Type: {definition.persona_type.value if definition.persona_type else '(none)'}")
    print(f"  Audio Influence: {definition.audio_influence}")
    print(f"  Style Influence: {definition.style_influence}")
    print(f"  Weirdness: {definition.weirdness}")
    print(f"  Cover of Track: {definition.cover_of_track_id or '(none)'}")
    print(f"  Created: {definition.created_at}")
    print(f"  Updated: {definition.updated_at}")

    if definition.links:
        print("  Links:")
        for link in definition.links:
            desc = f" - {link.description}" if link.description else ""
            print(f"    [{link.id}] {link.url}{desc}")

    if definition.comments:
        print(f"  Comments:\n    {definition.comments[:200]}")

    return 0


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new definition."""
    db = get_db()
    db.create_tables()
    repo = DefinitionRepository(db)

    try:
        data = DefinitionCreate(
            title=args.title,
            annotation=args.annotation,
            model=ModelVersion(args.model),
            style_of_music=args.style,
            lyrics=args.lyrics,
            persona_id=args.persona,
            persona_type=PersonaType(args.persona_type) if args.persona_type else None,
            vocals=VocalsType(args.vocals),
            audio_influence=args.audio_influence,
            style_influence=args.style_influence,
            weirdness=args.weirdness,
            comments=args.comments,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    definition = repo.create(data)
    print(f"Created definition #{definition.id}: {definition.title}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update a definition."""
    db = get_db()
    repo = DefinitionRepository(db)

    update_fields = {}
    if args.title is not None:
        update_fields["title"] = args.title
    if args.annotation is not None:
        update_fields["annotation"] = args.annotation
    if args.model is not None:
        update_fields["model"] = ModelVersion(args.model)
    if args.style is not None:
        update_fields["style_of_music"] = args.style
    if args.lyrics is not None:
        update_fields["lyrics"] = args.lyrics
    if args.vocals is not None:
        update_fields["vocals"] = VocalsType(args.vocals)
    if args.audio_influence is not None:
        update_fields["audio_influence"] = args.audio_influence
    if args.style_influence is not None:
        update_fields["style_influence"] = args.style_influence
    if args.weirdness is not None:
        update_fields["weirdness"] = args.weirdness
    if args.comments is not None:
        update_fields["comments"] = args.comments

    if not update_fields:
        print("Error: No fields to update", file=sys.stderr)
        return 1

    try:
        data = DefinitionUpdate(**update_fields)
        definition = repo.update(args.id, data)
    except DefinitionNotFoundError:
        print(f"Error: Definition {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Updated definition #{definition.id}: {definition.title}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a definition."""
    db = get_db()
    repo = DefinitionRepository(db)

    if not args.force:
        try:
            definition = repo.get(args.id)
        except DefinitionNotFoundError:
            print(f"Error: Definition {args.id} not found", file=sys.stderr)
            return 1

        response = input(f"Delete definition '{definition.title}'? [y/N] ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    if repo.delete(args.id):
        print(f"Deleted definition #{args.id}")
        return 0
    else:
        print(f"Error: Definition {args.id} not found", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search definitions."""
    db = get_db()
    repo = DefinitionRepository(db)

    results = repo.search(args.query, limit=args.limit)

    if not results:
        print(f"No definitions found matching '{args.query}'")
        return 0

    print(f"Found {len(results)} definition(s):\n")
    print(f"{'ID':<6} {'Title':<35} {'Model':<8} {'Style':<30}")
    print("-" * 79)

    for definition in results:
        style = definition.style_of_music or ""
        if len(style) > 27:
            style = style[:27] + "..."
        print(
            f"{definition.id:<6} {definition.title[:33]:<35} "
            f"{definition.model.value:<8} {style:<30}"
        )

    return 0


def cmd_add_link(args: argparse.Namespace) -> int:
    """Add a link to a definition."""
    db = get_db()
    repo = DefinitionRepository(db)

    try:
        definition = repo.add_link(args.id, args.url, args.description)
    except DefinitionNotFoundError:
        print(f"Error: Definition {args.id} not found", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Added link to definition #{definition.id}")
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
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
