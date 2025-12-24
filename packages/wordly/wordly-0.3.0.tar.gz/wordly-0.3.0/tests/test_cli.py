"""Test CLI commands."""

from __future__ import annotations

import sys
import errno
import subprocess
import textwrap
import unittest

USAGE_TEXT = textwrap.dedent("""\
    usage: Wordly [-h] [-v] [-p PORT] [-H HOSTNAME] words [words ...]
    Wordly: error: the following arguments are required: words
""")


class TestCLI(unittest.TestCase):
    """CLI test case."""

    def test_argument_required(self) -> None:
        """Should return usage text if no argument is provided."""
        result = subprocess.run(
            [sys.executable, "-m", "wordly"], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, errno.ENOENT)
        self.assertEqual("", result.stdout)
        self.assertIn(USAGE_TEXT, result.stderr)
