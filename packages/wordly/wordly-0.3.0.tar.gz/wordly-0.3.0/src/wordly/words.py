"""Wordly Utility classes for use in your python scripts."""

from __future__ import annotations

import asyncio
from collections import UserString
from collections.abc import Sequence

from wordly.client import DictClient
from wordly.status_codes import Status


class Word(UserString):
    """`str` subclass that provides an interface for retrieving definitions of terms."""

    def __init__(
        self,
        seq: Sequence[str],
        hostname: str = "dict.org",
        port: int = 2628,
        client: DictClient | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(seq)

        self.client = client or DictClient(hostname=hostname, port=port)
        self._cache = {}

    @property
    async def adefinition(self) -> str | None:
        """Return definition of word."""
        if not self._cache:
            data = await self.client.define(self.data)
            self._cache.update(data.mapping)
        if definition := self._cache.get(Status.DEFINITION.name):
            return definition.decode()

    @property
    def definition(self) -> str | None:
        """Return definition of word."""
        if not self._cache:
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(self.client.define(self.data))
            self._cache.update(data.mapping)
        if definition := self._cache.get(Status.DEFINITION.name):
            return definition.decode()
