import re

from .library import Library
from .model import Block, Entry, ExplicitComment, Field, ImplicitComment, Preamble, String


class Splitter:
    """Splitter class to split standardizing bib data list to library.

    Attributes:
        regex_block_type: Regular expression to match block type.
    """

    def __init__(self):
        self.regex_block_type = re.compile(r"@([a-zA-Z]+){")

    def splitter(self, data_list: list[str], implicit_coments: list[list[str]]):
        """Split standardizing bib data list to library."""
        _blocks = []

        _blocks.extend([ImplicitComment(i[0]) for i in implicit_coments if i])

        implicit_comment_blocks = []
        explicit_comment_blocks = []
        string_blocks = []
        preamble_blocks = []
        entry_blocks = []

        # Initialize
        data_list = "".join(data_list).splitlines(keepends=True)
        data_list = [line for line in data_list if line.strip()]

        line_index, len_data = 0, len(data_list)
        while line_index < len_data:
            line = data_list[line_index]
            line_index += 1

            if not (mch_block := self.regex_block_type.search(line)):
                implicit_comment_blocks.append(ImplicitComment(line, line_index))
                continue

            block_type = mch_block.group(1)
            if block_type == "comment":
                block, line_index = self._splitter_comment(block_type, line, line_index, len_data, data_list)
                if isinstance(block, Block):
                    explicit_comment_blocks.append(block)
                elif isinstance(block, str):
                    implicit_comment_blocks.append(ImplicitComment(block, line_index - 1))

            elif block_type == "string":
                block, line_index = self._splitter_string(block_type, line, line_index, len_data, data_list)
                if isinstance(block, Block):
                    string_blocks.append(block)
                elif isinstance(block, str):
                    implicit_comment_blocks.append(ImplicitComment(block, line_index - 1))

            elif block_type == "preamble":
                block, line_index = self._splitter_preamble(block_type, line, line_index, len_data, data_list)
                if isinstance(block, Block):
                    preamble_blocks.append(block)
                elif isinstance(block, str):
                    implicit_comment_blocks.append(ImplicitComment(block, line_index - 1))

            else:
                block, line_index, temp = self._splitter_entry(block_type, line, line_index, len_data, data_list)
                entry_blocks.append(block)
                implicit_comment_blocks.extend(temp)

        _blocks.extend(implicit_comment_blocks)
        _blocks.extend(explicit_comment_blocks)
        _blocks.extend(string_blocks)
        _blocks.extend(preamble_blocks)
        _blocks.extend(entry_blocks)
        return Library(_blocks)

    def _splitter_entry(self, block_type, line, line_idx, len_data, data_list) -> tuple[Block | str, int, list]:
        regex = re.compile(r"@([a-zA-Z]+){(.*),")
        if not (mch_entry := regex.search(line)):
            block = Entry(block_type, "", [], line_idx)
        else:
            block = Entry(mch_entry.group(1), mch_entry.group(2).strip(), [], line_idx)

        regex_field_type = re.compile(r"[%\s]*([\w\-]+)" + r'\s*=\s*["{](.*)["}][,]?\n', flags=re.I)
        regex_field_type_abbr = re.compile(r"[%\s]*([\w\-]+)" + r"\s*=\s*([\w\-]+)[,]?\n", flags=re.I)
        implicit_comment_blocks = []
        while line_idx < len_data:
            new_line = data_list[line_idx]
            if self.regex_block_type.match(new_line):
                break

            if mch := regex_field_type.match(new_line):
                block.set_field(Field(mch.group(1), mch.group(2), start_line=None))
            elif mch := regex_field_type_abbr.match(new_line):
                block.set_field(Field(mch.group(1), mch.group(2), start_line=None))
            elif (new_line.strip() == "}") or (new_line.strip() == ""):
                pass
            else:
                implicit_comment_blocks.append(ImplicitComment(new_line, line_idx))
            line_idx += 1

        if not block.key:
            block.key = self._generate_entry_key(block)
        return block, line_idx, implicit_comment_blocks

    @staticmethod
    def _generate_entry_key(entry: Entry) -> str:
        title = entry["title"] if "title" in entry else ""
        year = entry["year"] if "year" in entry else ""
        doi = entry["doi"] if "doi" in entry else ""
        author = entry["author"] if "author" in entry else ""
        keys = [entry.entry_type[:3]]
        if year:
            keys.append(year)
        if doi:
            keys.append(doi)
        if author:
            keys.append(author[:20])
        if title:
            keys.append(title[:70])

        citation_key = re.sub(r"\W", "", "_".join(keys).lower())[:80]
        while citation_key and citation_key[-1] == "_":
            citation_key = citation_key[:-1]
        return citation_key

    def _splitter_comment(self, block_type, line, line_idx, len_data, data_list) -> tuple[Block | str, int]:
        regex = re.compile(r"@comment{" + r"(.*)" + "}\n")
        if not (mch := regex.search(line)):
            return line, line_idx

        block = ExplicitComment(mch.group(1), line_idx)
        return block, line_idx

    def _splitter_string(self, block_type, line, line_idx, len_data, data_list) -> tuple[Block | str, int]:
        regex = re.compile(r"@string{" + r"\s*([\w]+)\s*=\s*" + r'(["{])' + r"([\w\-]+)" + r'(["}])' + "}\n")
        if not (mch := regex.search(line)):
            return line, line_idx

        block = String(mch.group(1), mch.group(3), line_idx)
        if not block.key:
            block.key = re.sub(r"\W", "", block.value.lower())[:80]
        return block, line_idx

    def _splitter_preamble(self, block_type, line, line_idx, len_data, data_list) -> tuple[Block | str, int]:
        regex = re.compile(r"@preamble{" + r'\s*(")' + r"([\w\-\\\[\]\{\}\s]+)" + r'(")\s*' + "}\n")
        if not (mch := regex.search(line)):
            return line, line_idx

        block = Preamble(mch.group(2), line_idx)
        return block, line_idx
