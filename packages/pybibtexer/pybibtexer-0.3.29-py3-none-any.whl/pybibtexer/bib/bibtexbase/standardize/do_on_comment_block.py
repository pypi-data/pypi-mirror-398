"""Comment block standardization utilities.

This module provides functionality for processing and standardizing BibTeX
comment blocks. Comment blocks in BibTeX are used for documentation and
notes that should be preserved but formatted consistently.

Classes:
    StandardizeCommentBlock: Handles the standardization of @comment blocks,
        ensuring proper brace matching and formatting.
"""

import re


class StandardizeCommentBlock:
    """Stanndardize comment block."""

    def __init__(self) -> None:
        pass

    def standardize(self, block: list[str]) -> tuple[list[str], list[list[str]]]:
        implicit_comments = []

        regex_comment = re.compile(r"@comment{" + r"(.*)", re.DOTALL)
        if mch := regex_comment.match("".join(block)):
            a = mch.group(1).strip()
            if (ll := (a.count("{") + 1)) > (lr := a.count("}")):
                a += "}" * (ll - lr)
            elif ll < lr:
                a = "{" * (lr - ll) + a

            if sub_mch := re.match(r"(.*)" + "}" + r"(.*)(\n*)", a):
                block = []

                sub_a, sub_b, sub_c = sub_mch.groups()
                if sub_a.strip():
                    block = ["@comment{" + sub_a.replace("\n", " ").strip() + "}\n"]

                if sub_b.strip():
                    implicit_comments = [[sub_b + sub_c, __class__.__name__]]

            else:
                block = []
                implicit_comments = [["".join(block), __class__.__name__]]
        else:
            block = []
            implicit_comments = [["".join(block), __class__.__name__]]
        return block, implicit_comments
