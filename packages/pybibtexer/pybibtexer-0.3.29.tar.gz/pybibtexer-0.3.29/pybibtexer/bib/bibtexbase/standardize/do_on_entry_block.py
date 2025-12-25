"""Entry block standardization utilities.

This module provides comprehensive functionality for processing and standardizing
BibTeX entry blocks. Entry blocks contain the actual bibliographic data and
require the most complex processing including field validation, formatting,
and error checking.

Classes:
    StandardizeEntryBlock: Main class for standardizing BibTeX entry blocks
        with configurable field lists and comprehensive validation.
    EntryBase: Base class providing utility methods for field extraction
        and brace/quote detection.
    SplitEntry: Handles splitting of entry blocks based on field patterns.
    AppendEntry: Manages field appending and line continuation processing.
    ExtractEntry: Extracts and validates field content from entry blocks.
    CheckEntry: Performs final validation and error checking on entry blocks.

Functions:
    add_brace_or_quote: Utility function for ensuring proper brace/quote
        matching in field values.
"""

import re

from ._base import split_data_list
from .default_data import DEFAULT_FIELDS_LIST, FIELD_FORMAT_FLAG


class StandardizeEntryBlock:
    """Stanndardize entry block.

    Args:
        default_additional_field_list (list[str] | None = None): Additional default fields.

    Attributes:
        default_fields_list (list[str]): Default fields.
    """

    def __init__(self, default_additional_field_list: list[str] | None = None) -> None:
        if default_additional_field_list is None:
            default_additional_field_list = []

        default_fields_old = [d.lower().strip() for d in DEFAULT_FIELDS_LIST]
        default_fields_new = [d.lower().strip() for d in default_additional_field_list]
        self.default_fields_list = list(set(default_fields_old).union(set(default_fields_new)))

    def standardize(self, block: list[str]) -> tuple[list[str], list[list[str]]]:
        # obtain braces or quotes
        implicit_comments = []
        pre, post = EntryBase().obtain_braces_or_quotes(block)
        if (len(pre) == 0) or (len(post) == 0):
            message = f"Obtain braces or quotes: No standard `pre - {pre}` and `post - {post}`"
            implicit_comments.append(["".join(block), message])
            return [], implicit_comments

        # Obtain fields
        # Support for abbreviations
        field_list = EntryBase().obtain_fields(block, self.default_fields_list)
        if len(field_list) == 0:
            message = "`Obtain fields`: No fields found"
            implicit_comments.append(["".join(block), message])
            return [], implicit_comments

        # Split according to the field pattern
        # Not support abbreviations: ['year = {2019}, journal = ECJ,']
        # TODO Support abbreviations
        pattern = r"\b((?:{})\s*=\s*(?:{}))".format("|".join(field_list), "|".join([rf"{pre}"]))  # compulsory
        block = SplitEntry().split_fields(pattern, block)

        # Append according to the field pattern
        # Support abbreviations
        block = AppendEntry().append_field(field_list, (pre, post), block)

        # Extract
        # Support abbreviations
        block, redundant_list = ExtractEntry().extract(field_list, (pre, post), block)
        if len(redundant_list) != 0:
            message = "`Extract`: Redundant content"
            implicit_comments.append(["".join(redundant_list), message])

        # Check
        # Support abbreviations
        error_dict, block, is_standard_bib_flag = CheckEntry().check(field_list, (pre, post), block)
        if len(error_dict) != 0:
            for key in error_dict:
                implicit_comments.append(["".join(error_dict[key]), f"`Check`: {key}"])

        if not is_standard_bib_flag:
            implicit_comments.append(["".join(block), "`Check`: Not standard bib"])
            return [], implicit_comments

        return block, implicit_comments


class EntryBase:
    def __init__(self) -> None:
        pass

    @staticmethod
    def obtain_braces_or_quotes(block: list[str]) -> tuple[str, str]:
        """Obtain braces or quotes in block.

        Args:
            block (list[str]): block.

        Returns:
            tuple[str, str]: the tuple of braces or quotes.
        """
        content = "".join(block)
        regex_list = [
            re.compile(r'\btitles*\s*=\s*([{"])', flags=re.I),
            re.compile(r'\bauthors*\s*=\s*([{"])', flags=re.I),
            re.compile(r'\byears*\s*=\s*([{"])', flags=re.I),
            re.compile(r'\bpages*\s*=\s*([{"])', flags=re.I),
            re.compile(r'\burls*\s*=\s*([{"])', flags=re.I),
        ]
        flag_list_list = [sorted(set(regex.findall(content))) for regex in regex_list]

        flag_list_list = [f for f in flag_list_list if len(f) != 0]
        len_list = [len(f) for f in flag_list_list]

        # 0 or 1 or 2 flags
        if (len(len_list) == 0) or (2 in len_list) or (not all(f == flag_list_list[0] for f in flag_list_list)):
            return "", ""

        if flag_list_list[0][0] == "{":
            return "{", "}"
        else:
            return '"', '"'

    def obtain_fields(
        self, block: list[str], default_fields_list: list[str], field_pattern: str = r"[\w\-]+"
    ) -> list[str]:
        r"""Obtain fileds in block.

        Args:
            block (list[str]): block.
            field_pattern (str = r'[\w\-]+'): field pattern.

        Returns:
            list[str]: field list.
        """
        regex = re.compile(rf"({field_pattern})\s*=\s*(?:{'|'.join(FIELD_FORMAT_FLAG)})")  # support for abbreviation
        obtain_field_list = list(set(regex.findall("".join(block))))
        obtain_field_list = [field for field in obtain_field_list if field.lower() in default_fields_list]
        return sorted(obtain_field_list)


class SplitEntry:
    def __init__(self) -> None:
        super().__init__()

    def split_fields(self, field_pattern: str, block: list[str], last_next: str = "next") -> list[str]:
        return split_data_list(field_pattern, block, last_next)


class AppendEntry:
    """Append Patch Bib."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def append_field(field_list: list[str], braces_or_quotes: tuple[str, str], block: list[str]) -> list[str]:
        """Append.

        Args:
            field_list (list[str]): Append field list.
            braces_or_quotes (tuple[str, str]): Brace or quote.
            block (list[str]): Data list.

        Returns:
            list[str]: new patch bib after appending.
        """
        pre, _ = braces_or_quotes

        temp = rf"[%\s]*(?:{'|'.join(field_list)})"
        regex_field = re.compile(rf"{temp}\s*=\s*{pre}", flags=re.I)
        regex_field_abbr = re.compile(rf"{temp}\s*=\s*\w+[\w\-]*", flags=re.I)  # journal = EJC,
        regex_termination = re.compile(r"\s*@[a-zA-Z]*{", flags=re.I)

        # strip and append
        line_index, len_data, new_block = 0, len(block), []
        while line_index < len_data:
            line = block[line_index]
            line_index += 1
            if regex_field.match(line) or regex_termination.match(line) or regex_field_abbr.match(line):
                new_line = line
                while line_index < len_data:
                    line = block[line_index]
                    if regex_field.match(line) or regex_termination.match(line) or regex_field_abbr.match(line):
                        break
                    else:
                        if line.lstrip():
                            new_line = new_line.rstrip() + " " + line.lstrip()  # append
                        line_index += 1
                new_block.append(new_line)
            else:
                new_block.append(line)
        return new_block


class ExtractEntry:
    def __init__(self) -> None:
        pass

    def extract(
        self, field_list: list[str], brace_or_quote: tuple[str, str], block: list[str]
    ) -> tuple[list[str], list[str]]:
        """Extract.

        Args:
            field_list (list[str]): field list
            brace_or_quote (tuple[str, str]): (", ") or ({, })
            block (list[str]): the block

        Return:
            tuple[list[str], list[str]]: main block, redundant part
        """
        pre, post = brace_or_quote

        temp = rf"[%\s]*(?:{'|'.join(field_list)})"
        regex_field_two = re.compile(rf"({temp}\s*=\s*{pre})(.*)(\n*)", flags=re.I)
        regex_field_one = re.compile(rf"({temp}\s*=\s*{pre}.*{post})(.*)(\n*)", flags=re.I)
        regex_field_abbr = re.compile(rf"({temp}\s*=\s*\w+[\w\-]*)(.*)(\n*)", flags=re.I)
        regex_termination = re.compile(r"(\s*@[a-zA-Z]*{\s*[\w\-:/\\.\']*)(.*)(\n*)", flags=re.I)

        main_list, redundant_list = [], []

        for line in block:
            new_line, redundant = "", ""
            if mch := regex_termination.match(line):
                one, two, three = mch.groups()
                new_line = one + ",\n"
                if re.sub(r"[\s,\n\}]+", "", two):
                    redundant = two + three

            elif mch := regex_field_abbr.match(line):
                one, two, three = mch.groups()
                new_line = one + ",\n"
                if re.sub(r"[\s,\n\}]+", "", two):
                    redundant = two + three

            elif mch := regex_field_one.match(line):
                one, two, three = mch.groups()
                new_line = self._resub_brace_or_quote(pre, post, one + ",\n")
                if re.sub(r"[\s,\n\}]+", "", two):
                    redundant = two + three

            elif mch := regex_field_two.match(line):
                one, two, three = mch.groups()
                new_line = self._resub_brace_or_quote(pre, post, one + two.strip() + post + ",\n")

            elif line.strip() == "}":
                pass

            else:
                return [], block

            if new_line:
                main_list.append(new_line)
            if redundant:
                redundant_list.append(redundant)

        # for enclosing "@[a-zA-Z]{"
        if main_list:
            main_list.append("}\n")
        return main_list, redundant_list

    def _resub_brace_or_quote(self, pre, post, line: str) -> str:
        if post == "}":
            if line.count(post) > line.count(pre):
                line = re.sub(r"(}[}\s\n,]*)$", "},\n", line)
                line = add_brace_or_quote(pre, post, line)

        elif post == '"':
            if line.count(post) > line.count(pre):
                line = re.sub(r'("["\s\n,]*)$', '",\n', line)
                line = add_brace_or_quote(pre, post, line)
        return line


def add_brace_or_quote(pre, post, line: str):
    if (cpre := line.count(pre)) != (cpost := line.count(post)):
        line_list = list(line)
        if cpre > cpost:
            line_list = line_list[::-1]
            line_list.insert(line_list.index(post), post * (cpre - cpost))
            line_list = line_list[::-1]
        else:
            line_list.insert(line.index(pre), pre * (cpost - cpre))

        line = "".join(line_list)
    return line


class CheckEntry:
    @staticmethod
    def check(
        field_list: list[str], brace_or_quote: tuple[str, str], block: list[str]
    ) -> tuple[dict[str, list[str]], list[str], bool]:
        """Check."""
        pre, post = brace_or_quote

        regex_entry = re.compile(r"\s*@[a-zA-Z]+{")
        regex_field = re.compile(rf"\s*(?:{'|'.join(field_list)})" + r"\s*=")
        entry_flag, brace_flag = False, False  # minimal conditions
        error_dict: dict[str, list[str]] = {}
        new_block = []
        for line in block:
            if regex_entry.match(line) and (not entry_flag):  # just iff exsiting one time in single patch bib
                if (line.count("{") != 1) or (line.count(",") != 1):
                    error_dict.setdefault("Failed entry_type", []).append(line)
                else:
                    entry_flag = True
                    new_block.append(line)

            elif regex_field.match(line):
                new_block.append(add_brace_or_quote(pre, post, line))

            elif (line.strip() == "}") and (not brace_flag):  # just iff exsiting one time in single patch bib
                brace_flag = True
                new_block.append(line)

            else:
                error_dict.setdefault("Redundant content`", []).append(line)
        return error_dict, new_block, entry_flag and brace_flag


if __name__ == "__main__":
    pass
