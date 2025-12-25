"""String block standardization utilities.

This module provides functionality for processing and standardizing BibTeX
string blocks. String blocks define abbreviations and macros that can be
used throughout the BibTeX file to maintain consistency and reduce redundancy.

Classes:
    StandardizeStringBlock: Handles the standardization of @string blocks,
        ensuring proper delimiter matching and formatting of string definitions.
"""

import re


class StandardizeStringBlock:
    """Stanndardize string block."""

    def __init__(self) -> None:
        pass

    def standardize(self, block: list[str]) -> tuple[list[str], list[list[str]]]:
        implicit_comments = []

        regex = re.compile(
            r"@string{" + r"\s*([\w]+)\s*=\s*" + r'(["{])' + r"([\w\-\n]+)" + r'(["}])' + r"(.*)(\n*)", re.DOTALL
        )
        if mch := regex.match("".join(block)):
            a, b, c, d, e, f = mch.groups()
            if ((b == '"') and (d == '"')) or ((b == "{") and (d == "}")):
                block = ["@string{" + a + " = " + b + c.replace("\n", " ").strip() + d + "}\n"]

                if e and e.lstrip()[0] == "}":
                    e = e.lstrip()[1:].lstrip()

                if e.strip():
                    implicit_comments = [[e + f, __class__.__name__]]

            else:
                block = []
                implicit_comments = [["".join(block), __class__.__name__]]
        else:
            block = []
            implicit_comments = [["".join(block), __class__.__name__]]
        return block, implicit_comments
