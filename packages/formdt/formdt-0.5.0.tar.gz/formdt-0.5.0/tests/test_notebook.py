import json
import tempfile
from pathlib import Path


from formdt.config import Config
from formdt.notebook import format_notebook


def create_test_notebook(cells: list[dict]) -> Path:
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": cells}
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False)
    json.dump(notebook, tmp)
    tmp.close()
    return Path(tmp.name)


class TestNotebookFormatting:
    def test_formats_all_markdown_cells(self):
        path = create_test_notebook(
            [
                {
                    "cell_type": "markdown",
                    "source": [
                        "This is a long line that should be wrapped at forty characters."
                    ],
                    "metadata": {},
                },
                {"cell_type": "code", "source": ["print('hello')"], "metadata": {}},
                {
                    "cell_type": "markdown",
                    "source": ["Another long markdown line that should be wrapped."],
                    "metadata": {},
                },
            ]
        )
        config = Config(line_length=40)

        result = format_notebook(path, config, all_markdown=True)

        md_cells = [c for c in result["cells"] if c["cell_type"] == "markdown"]
        for cell in md_cells:
            text = "".join(cell["source"])
            for line in text.split("\n"):
                assert len(line) <= 40

    def test_formats_specific_cells_by_index(self):
        path = create_test_notebook(
            [
                {
                    "cell_type": "markdown",
                    "source": ["Cell zero with a very long line of text."],
                    "metadata": {},
                },
                {
                    "cell_type": "markdown",
                    "source": ["Cell one unchanged."],
                    "metadata": {},
                },
                {
                    "cell_type": "markdown",
                    "source": ["Cell two with a very long line of text."],
                    "metadata": {},
                },
            ]
        )
        config = Config(line_length=20)

        result = format_notebook(path, config, cells=[0, 2])

        assert "\n" in "".join(result["cells"][0]["source"])
        assert "".join(result["cells"][1]["source"]) == "Cell one unchanged."
        assert "\n" in "".join(result["cells"][2]["source"])

    def test_ignores_code_cells(self):
        path = create_test_notebook(
            [
                {
                    "cell_type": "code",
                    "source": [
                        "def very_long_function_name_that_exceeds_limit(): pass"
                    ],
                    "metadata": {},
                },
            ]
        )
        config = Config(line_length=20)

        result = format_notebook(path, config, all_markdown=True)

        assert result["cells"][0]["source"] == [
            "def very_long_function_name_that_exceeds_limit(): pass"
        ]

    def test_no_changes_without_flags(self):
        path = create_test_notebook(
            [
                {
                    "cell_type": "markdown",
                    "source": ["This line should remain unchanged."],
                    "metadata": {},
                },
            ]
        )
        config = Config(line_length=10)

        result = format_notebook(path, config)

        assert result["cells"][0]["source"] == ["This line should remain unchanged."]


class TestLinkPreservation:
    def test_preserves_links_in_markdown(self):
        from formdt.formatter import format_markdown

        config = Config(line_length=40)
        text = "Check out [this documentation](https://example.com/very/long/path/to/docs) for more info."
        result = format_markdown(text, config)

        assert (
            "[this documentation](https://example.com/very/long/path/to/docs)" in result
        )

    def test_link_stays_intact_across_wrap(self):
        from formdt.formatter import format_markdown

        config = Config(line_length=30)
        text = "See [link](https://example.com) here."
        result = format_markdown(text, config)

        assert "[link](https://example.com)" in result
