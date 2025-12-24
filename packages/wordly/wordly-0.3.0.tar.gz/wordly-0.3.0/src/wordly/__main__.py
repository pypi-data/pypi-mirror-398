"""Module entry point."""

from __future__ import annotations

import asyncio

from wordly.cli import main


def run() -> None:
    """Run async cli."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
