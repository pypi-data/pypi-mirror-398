"""Command line application module.

Parses command line arguments passed to the app and prints word definitions.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from wordly import __app_description__, __app_name__, __epilog__, __version__
from wordly.client import DictClient


async def print_definition(word: str, hostname: str, port: int) -> str:
    """Print definitions to stdout."""
    async with DictClient(hostname=hostname, port=port) as client:
        response = await client.define(word)
        return response.definition


async def main(argv: Sequence[str] | None = None) -> None:
    """Run command line application."""
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description=__app_description__,
        epilog=__epilog__,
    )
    opt = parser.add_argument

    opt("words", nargs="+", help="One or more words to define.")
    opt("-v", "--version", version=__version__, action="version")
    opt(
        "-p",
        "--port",
        type=int,
        default=2628,
        help="Specify the port number. Default: 2628",
    )
    opt(
        "-H",
        "--hostname",
        type=str,
        default="dict.org",
        help="Specify the server. Default: dict.org",
    )

    args = vars(parser.parse_args(argv))

    tasks = [
        print_definition(word, args["hostname"], args["port"]) for word in args["words"]
    ]

    definitions = await asyncio.gather(*tasks)
    print(*definitions)
