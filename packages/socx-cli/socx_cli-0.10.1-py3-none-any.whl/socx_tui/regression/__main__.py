"""Entrypoint helpers for launching the Textual-based SoCX TUI application."""

from .app import SoCX


def main() -> int:
    """Start the TUI application and return the process exit status."""
    app = SoCX()
    return app.run(inline=True)


if __name__ == "__main__":
    main()
