from __future__ import annotations

import argparse
from pathlib import Path

from .importer import (
    DEFAULT_PREFIX,
    ImporterError,
    exit_with_error,
    extract_item_sets,
    install_item_sets,
    load_champion_map,
    load_source,
    summarize_item_sets,
    write_export,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wrasul-lol-items",
        description="Import Wrasul League of Legends item build JSON into local item set files.",
    )
    parser.add_argument("--source", required=True, help="Bilibili opus URL, local JSON file, or text file containing JSON.")
    parser.add_argument("--lol-dir", help="League of Legends root directory, for example C:\\Riot Games\\League of Legends.")
    parser.add_argument("--output", help="Optional path to export the extracted normalized JSON.")
    parser.add_argument("--install", action="store_true", help="Actually write item set files. Without this, only dry-run.")
    parser.add_argument(
        "--target",
        choices=["champion", "global"],
        default="champion",
        help="Install to champion-specific folders by default, or one global folder.",
    )
    parser.add_argument("--champion-map", help="Optional JSON map for champion id to Data Dragon champion key.")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Filename prefix for generated item set files.")
    parser.add_argument("--keep-old", action="store_true", help="Do not remove older files generated with the same prefix.")
    parser.add_argument(
        "--allow-running-client",
        action="store_true",
        help="Allow installation while the League client appears to be running.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        item_sets = extract_item_sets(load_source(args.source))
        print(f"Loaded: {summarize_item_sets(item_sets)}")

        if args.output:
            output = Path(args.output)
            write_export(item_sets, output)
            print(f"Exported normalized JSON: {output}")

        champion_map = None
        if args.lol_dir and args.target == "champion":
            champion_map = load_champion_map(Path(args.champion_map) if args.champion_map else None)
            print(f"Loaded champion map: {len(champion_map)} champions")

        if args.lol_dir:
            result = install_item_sets(
                item_sets,
                Path(args.lol_dir),
                champion_map=champion_map,
                target=args.target,
                prefix=args.prefix,
                install=args.install,
                replace_old=not args.keep_old,
                allow_running_client=args.allow_running_client,
            )
            action = "Installed" if args.install else "Dry-run planned"
            print(f"{action}: {len(result.written) if args.install else len(result.planned)} files")
            if result.backup_dir:
                print(f"Backup: {result.backup_dir}")
            for path in (result.written if args.install else result.planned)[:20]:
                print(f"- {path}")
            shown = len(result.written if args.install else result.planned)
            if shown > 20:
                print(f"... {shown - 20} more files")
        elif args.install:
            raise ImporterError("--install requires --lol-dir")
        else:
            print("No --lol-dir provided, so no game files were changed.")

    except ImporterError as exc:
        return exit_with_error(str(exc))
    return 0
