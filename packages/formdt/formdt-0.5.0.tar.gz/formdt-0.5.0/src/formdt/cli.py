import argparse
import sys
from pathlib import Path

from .config import load_config
from .formatter import format_markdown
from .notebook import format_notebook, write_notebook


def parse_cells(value: str) -> list[int]:
    cells = []
    for part in value.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            cells.extend(range(int(start), int(end) + 1))
        else:
            cells.append(int(part))
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="formdt", description="Format markdown files with configurable line length"
    )
    parser.add_argument(
        "file", type=Path, help="Markdown or Jupyter notebook file to format"
    )
    parser.add_argument(
        "-l",
        "--line-length",
        type=int,
        help="Override line length (default: from .formdt or 80)",
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Write changes back to file (default: print to stdout)",
    )
    parser.add_argument(
        "-c",
        "--cells",
        type=str,
        help="Cell indices to format (e.g., '0,2,5' or '1-3,7'). Notebook only.",
    )
    parser.add_argument(
        "-m",
        "--markdown",
        action="store_true",
        help="Format all markdown cells. Notebook only.",
    )

    args = parser.parse_args()

    config = load_config()
    if args.line_length:
        config.line_length = args.line_length

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    if args.file.suffix == ".ipynb":
        cells = parse_cells(args.cells) if args.cells else None
        notebook = format_notebook(
            args.file, config, cells=cells, all_markdown=args.markdown
        )

        if args.write:
            write_notebook(notebook, args.file)
        else:
            import json

            print(json.dumps(notebook, indent=1, ensure_ascii=False))
    else:
        content = args.file.read_text()
        formatted = format_markdown(content, config)

        if args.write:
            args.file.write_text(formatted)
        else:
            print(formatted)

    return 0


if __name__ == "__main__":
    sys.exit(main())
