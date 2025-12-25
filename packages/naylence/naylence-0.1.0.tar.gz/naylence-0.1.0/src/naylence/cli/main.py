from __future__ import annotations

import argparse
from typing import Sequence

from naylence import __version__
from naylence.cli.commands.init import run_init


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="naylence", description="Naylence CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init", help="Scaffold a new Naylence project from a starter"
    )
    init_parser.add_argument("target_dir", nargs="?", help="Target directory")
    init_parser.add_argument("--template", help="Template id")
    init_parser.add_argument("--flavor", help="Template flavor")
    init_parser.add_argument("--list", action="store_true", help="List available templates")
    init_parser.add_argument("--ref", help="Git ref for starters repository")
    init_parser.add_argument("--from-local", action="store_true", help="Use local starters path")
    init_parser.add_argument("--from-github", action="store_true", help="Fetch starters from GitHub")
    init_parser.add_argument("--no-overwrite", dest="no_overwrite", action="store_true", help="Do not overwrite existing files (default)")
    init_parser.add_argument("--overwrite", dest="no_overwrite", action="store_false", help="Allow writing into non-empty directories")
    init_parser.set_defaults(no_overwrite=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
