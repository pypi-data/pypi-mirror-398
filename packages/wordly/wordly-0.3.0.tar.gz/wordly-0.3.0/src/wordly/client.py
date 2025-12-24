"""DICT client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from wordly.parser import DictParser
from wordly.status_codes import Status

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from types import TracebackType
    from typing import Self


class DictClient:
    """Client."""

    def __init__(
        self, hostname: str = "dict.org", port: int = 2628, READ_BYTES: int = 1024
    ) -> None:
        """Initialize."""
        self.hostname = hostname
        self.port = port
        self.line_reader = DictParser()
        self.parsers = [self.line_reader]
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None
        self.READ_BYTES = READ_BYTES

    def __repr__(self) -> str:
        """Return string representation of `DictClient`."""
        return f"{self.__class__.__name__}({self.hostname=}, {self.port=})"

    async def __aenter__(self) -> Self:
        """Enter method for async context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc: type[BaseException],
        tb: type[TracebackType],
    ) -> None:
        """Exit method for async context manager."""
        await self.disconnect()

    async def connect(self) -> tuple[StreamReader, StreamWriter]:
        """Upon successful connection a status code of 220 is expected."""
        self.reader, self.writer = await asyncio.open_connection(
            self.hostname, self.port
        )
        connection_info = await self.reader.read(self.READ_BYTES)
        self.line_reader.feed(connection_info)

        if Status.INITIAL_CONNECTION.name in self.line_reader.mapping:
            return self.reader, self.writer

        raise ConnectionError(f"Could not connect to: {self.hostname=}, {self.port=}")

    async def disconnect(self) -> None:
        """Close client connection."""
        self.writer.write(b"QUIT\r\n")
        await self.writer.drain()
        while Status.CLOSING_CONNECTION.name not in self.line_reader.mapping:
            closing_data = await self.reader.read(self.READ_BYTES)
            for line_reader in self.parsers:
                line_reader.feed(closing_data)
        self.writer.close()
        await self.writer.wait_closed()

    async def _send(self, command: bytes) -> DictParser:
        """Return line reader given a command."""
        if None in (self.reader, self.writer):
            self.reader, self.writer = await self.connect()
        else:
            new_line_reader = DictParser()
            new_line_reader.mapping[Status.INITIAL_CONNECTION.name] = (
                self.line_reader.mapping[Status.INITIAL_CONNECTION.name]
            )
            self.line_reader = new_line_reader
            self.parsers.append(self.line_reader)

        self.writer.write(command)
        await self.writer.drain()

        while (
            Status.COMMAND_COMPLETE.name not in self.line_reader.mapping
            and Status.NO_MATCH.name not in self.line_reader.mapping
        ):
            command_data = await self.reader.read(self.READ_BYTES)
            self.line_reader.feed(command_data)
        return self.line_reader

    async def define(self, word: str, database: str = "!") -> DictParser:
        """Return line reader given word and database."""
        command = f"DEFINE {database} {word}\r\n".encode()
        return await self._send(command)

    async def help(self) -> DictParser:
        """Return line reader with helpful information."""
        command = b"HELP\r\n"
        return await self._send(command)

    async def match(
        self, word: str, database: str = "*", strategy: str = "."
    ) -> DictParser:
        """Match a word in a database using a strategy."""
        command = f"MATCH {database} {strategy} {word}".encode()
        return await self._send(command)

    async def show(self, option: str = "DB") -> DictParser:
        """Show more information."""
        command = f"SHOW {option}".encode()
        return await self._send(command)
