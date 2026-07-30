"""Command-line entry point for dotenv-merge-cli."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import merge_env_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dotenv-merge-cli",
        description=(
            "Merge two or more .env-style files into one, with later "
            "files overriding earlier keys."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="env files to merge, in order (base file first, later files override)",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="write the merged result to PATH instead of stdout",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow --out to overwrite an existing file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(args.files) < 2:
        print("dotenv-merge-cli: need at least two files to merge", file=sys.stderr)
        return 2

    file_pairs: list[tuple[str, str]] = []
    for file_path in args.files:
        path = Path(file_path)
        try:
            text = path.read_text()
        except OSError as exc:
            print(f"dotenv-merge-cli: cannot read {file_path}: {exc}", file=sys.stderr)
            return 1
        file_pairs.append((path.name, text))

    merged = merge_env_files(file_pairs)

    if args.out:
        out_path = Path(args.out)
        if out_path.exists() and not args.force:
            print(
                f"dotenv-merge-cli: {args.out} already exists, use --force to overwrite",
                file=sys.stderr,
            )
            return 1
        try:
            out_path.write_text(merged)
        except OSError as exc:
            print(f"dotenv-merge-cli: cannot write {args.out}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(merged)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
