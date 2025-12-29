from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from rich.syntax import Syntax
from textual.widgets import Static
from textual.worker import get_current_worker
from textual.containers import ScrollableContainer
from textual.reactive import var


class PreviewWindow(ScrollableContainer):
    """Widget to show a preview of a file.

    A scrollable container that contains a
    [Rich Syntax](https://rich.readthedocs.io/en/latest/syntax.html) object
    which highlights and formats text.

    """

    ALLOW_MAXIMIZE = True
    DEFAULT_CSS = """
    PreviewWindow {
        width: 1fr;
        height: 1fr;
        border: heavy blank;
        overflow-y: scroll;
        &:focus { border: heavy ansi_blue; }
        #content { width: auto; }
        &.-preview-unavailable {
            overflow: auto;
            hatch: right ansi_black;
            align: center middle;
            text-style: bold;
            color: ansi_red;
        }
    }
    """
    DEFAULT_CLASSES = "-ansi-scrollbar"

    path: var[Path] = var(Path)

    @work(exclusive=True)
    async def update_syntax(self, path: Path) -> None:
        """Update the preview in a worker.

        A worker runs the code in a concurrent asyncio Task.

        Args:
            path: A Path to the file to get the content for.
        """
        worker = get_current_worker()
        content = self.query_one("#content", Static)
        if path.is_file():
            _file_type, encoding = mimetypes.guess_type(str(path))

            # A text file, we can attempt to syntax highlight it
            def read_lines() -> list[str] | None:
                """Read lines from a path in another thread."""
                try:
                    with open(path, encoding=encoding or "utf-8") as text_file:
                        return text_file.readlines(1024 * 32)
                except Exception:
                    # We could be more precise with error handling here, but
                    # for now we will treat all errors as fails.
                    return None

            # Read the lines in a thread so as not to pause the UI
            lines = await asyncio.to_thread(read_lines)
            if lines is None:
                self.call_later(content.update, "Preview not available")
                self.add_class("-preview-unavailable")
                return

            if worker.is_cancelled:
                return

            code = "".join(lines)
            lexer = Syntax.guess_lexer(str(path), code)
            try:
                syntax = Syntax(
                    code,
                    lexer,
                    word_wrap=False,
                    indent_guides=True,
                    line_numbers=True,
                    theme="ansi_light",
                )
            except Exception:
                return
            content.update(syntax)
            self.remove_class("-preview-unavailable")

    def watch_path(self, path: Path) -> None:
        self.update_syntax(path)

    def compose(self) -> ComposeResult:
        yield Static("", id="content")
