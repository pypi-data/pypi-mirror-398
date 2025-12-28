import json
from pathlib import Path

from .config import Config
from .formatter import format_markdown


def format_notebook(
    path: Path,
    config: Config,
    cells: list[int] | None = None,
    all_markdown: bool = False,
) -> dict:
    with open(path) as f:
        notebook = json.load(f)

    for i, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue

        if cells is not None and i not in cells:
            continue

        if not all_markdown and cells is None:
            continue

        source = cell.get("source", [])
        if isinstance(source, list):
            text = "".join(source)
        else:
            text = source

        formatted = format_markdown(text, config)
        cell["source"] = formatted.splitlines(keepends=True)
        if cell["source"] and not cell["source"][-1].endswith("\n"):
            pass

    return notebook


def write_notebook(notebook: dict, path: Path) -> None:
    with open(path, "w") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")
