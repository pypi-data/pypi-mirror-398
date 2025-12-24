"""DICT parser or line reader."""

from __future__ import annotations

from collections import defaultdict

from wordly.status_codes import Status


class DictParser:
    """Line reader for parsing byte stream of DICT protocol.

    Creates a map of DICT status code and associated information.
    """

    def __init__(self, delimiter: bytes = b"\r\n") -> None:
        """Initialize."""
        self.line = bytearray()
        self.mapping = defaultdict(bytearray)
        self.DELIMITER = delimiter

    def _process_line(self, ending: bytes = b"") -> None:
        """Process line."""
        code = self.line[:3]
        status = Status.by_value(bytes(code))

        if status:
            data = self.line[4:]
            self.part = status.name
        else:
            data = self.line

        buf = self.mapping[self.part]
        buf.extend(data)
        buf.extend(ending)

    def feed(self, stream: bytes) -> None:
        """Feed stream of `bytes` to line reader.

        Calls `_process_line` on bytes stream until delimiter
        can no longer be found.
        """
        split = stream.split(self.DELIMITER, 1)
        while len(split) > 1:
            old, new = split
            self.line += old
            self._process_line(b"\n")
            self.line = b""
            split = new.split(self.DELIMITER, 1)

        if line := split[0]:
            self.line += line
            self._process_line()
            self.line = b""

    @property
    def definition(self) -> str:
        """Return the definition of a term from parsed content."""
        return self.mapping.get(Status.DEFINITION.name, b"").decode()
