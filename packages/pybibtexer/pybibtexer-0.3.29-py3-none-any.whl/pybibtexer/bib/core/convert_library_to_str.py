from copy import deepcopy
from typing import Any

from ..bibtexparser import (
    BibtexFormat,
    Block,
    DuplicateBlockKeyBlock,
    Entry,
    ExplicitComment,
    Field,
    ImplicitComment,
    Library,
    MiddlewaresLibraryToStr,
    ParsingFailedBlock,
    Preamble,
    String,
)
from .convert_library_to_library import ConvertLibrayToLibrary

VAL_SEP = " = "
PARSING_FAILED_COMMENT = "% WARNING Parsing failed for the following {n} lines."


class ConvertLibrayToStr:
    """Convert library to str.

    Args:
        options (dict[str, Any]): Options. Default is {}.

    Attributes:
        is_standardize_library (bool): Is standardize library. Default is False.
        empty_entry_cite_keys (bool): Empty entry cite keys. Default is False.
        add_index_to_entries (bool): Add index to entries. Default is False.
        entries_necessary (bool): Is the entries are necessary in the bib file.
    """

    def __init__(self, options: dict[str, Any]):
        self.is_standardize_library = options.get("is_standardize_library", False)
        self.empty_entry_cite_keys = options.get("empty_entry_cite_keys", False)
        self.add_index_to_entries = options.get("add_index_to_entries", False)
        self.entries_necessary = options.get("entries_necessary", True)

        self.options = options

    def generate_str(self, library: Library | list[Block], bibtex_format: BibtexFormat | None = None) -> list[str]:
        """Serialize a BibTeX database.

        :param library: BibTeX database to serialize.
        :param bibtex_format: Customized BibTeX format to use (optional).
        """
        # --------- --------- --------- #
        if not isinstance(library, Library):
            library = Library(library)

        # standardizer
        if self.is_standardize_library:
            library = ConvertLibrayToLibrary(self.options).generate_single_library(library)

        # --------- --------- --------- #
        library = MiddlewaresLibraryToStr(self.options).functions(library)

        # --------- --------- --------- #
        if bibtex_format is None:
            bibtex_format = BibtexFormat()

        if bibtex_format.value_column == "auto":
            auto_val: int = self._calculate_auto_value_align(library)
            # Copy the format instance to avoid modifying the original
            # (which would be bad if the format is used for multiple libraries)
            bibtex_format = deepcopy(bibtex_format)
            bibtex_format.value_column = auto_val

        # --------- --------- --------- #
        if self.entries_necessary:
            if not library.entries:
                return []

        data_list = []
        j = 0
        for i, block in enumerate(library.blocks):
            if self.add_index_to_entries and isinstance(block, Entry):
                data_list.append(f"% {j + 1}\n")
                j += 1

            # Get str representation of block
            pieces = self._treat_block(bibtex_format, block)
            data_list.extend(pieces)

            # Separate Blocks
            if i < len(library.blocks) - 1:
                data_list.append(bibtex_format.block_separator)
        return data_list

    @staticmethod
    def _calculate_auto_value_align(library: Library) -> int:
        max_key_len = 0
        for entry in library.entries:
            for key in entry.fields_dict:
                max_key_len = max(max_key_len, len(key))
        return max_key_len

    def _treat_block(self, bibtex_format, block) -> list[str]:
        if isinstance(block, Entry):
            pieces = self._treat_entry(block, bibtex_format)
        elif isinstance(block, String):
            pieces = self._treat_string(block, bibtex_format)
        elif isinstance(block, Preamble):
            pieces = self._treat_preamble(block, bibtex_format)
        elif isinstance(block, ExplicitComment):
            pieces = self._treat_expl_comment(block, bibtex_format)
        elif isinstance(block, ImplicitComment):
            pieces = self._treat_impl_comment(block, bibtex_format)
        elif isinstance(block, ParsingFailedBlock):
            pieces = self._treat_failed_block(block, bibtex_format)
        else:
            raise ValueError(f"Unknown block type: {type(block)} in {__file__}")
        return pieces

    # entry
    def _treat_entry(self, block: Entry, bibtex_format: BibtexFormat) -> list[str]:
        if self.empty_entry_cite_keys:
            result = ["@" + block.entry_type + "{" + " " + ",\n"]
        else:
            result = ["@" + block.entry_type + "{" + block.key + ",\n"]
        field: Field
        for i, field in enumerate(block.fields):
            res = []
            res.append(bibtex_format.indent)
            res.append(field.key)
            res.append(self._val_intent_string(bibtex_format, field.key))
            res.append(VAL_SEP)
            res.append("{")  # add by me
            res.append(field.value)
            res.append("}")  # add by me
            if bibtex_format.trailing_comma or i < len(block.fields) - 1:
                res.append(",")
            res.append("\n")
            result.append("".join(res))

        result.append("}\n")
        return result

    @staticmethod
    def _val_intent_string(bibtex_format: BibtexFormat, key: str) -> str:
        """Calculate the spaces which have to be added after the ` = `."""
        if isinstance(bibtex_format.value_column, int):
            length = bibtex_format.value_column - len(key)
            return "" if length <= 0 else " " * length
        else:
            return ""

    # string
    @staticmethod
    def _treat_string(block: String, bibtex_format: BibtexFormat) -> list[str]:
        result = ["@string{", block.key, VAL_SEP, "{", block.value, "}", "}\n"]
        return ["".join(result)]

    # preamble
    @staticmethod
    def _treat_preamble(block: Preamble, bibtex_format: BibtexFormat) -> list[str]:
        result = ["@preamble{" + f' "{block.value.rstrip()} "' + " }", "\n"]
        return ["".join(result)]

    # implicit comment
    @staticmethod
    def _treat_impl_comment(block: ImplicitComment, bibtex_format: BibtexFormat) -> list[str]:
        # Note: No explicit escaping is done here - that should be done in middleware
        result = [block.comment.rstrip(), "\n"]
        return ["".join(result)]

    # explicit comment
    @staticmethod
    def _treat_expl_comment(block: ExplicitComment, bibtex_format: BibtexFormat) -> list[str]:
        result = ["@comment{", block.comment.rstrip(), "}\n"]
        return ["".join(result)]

    # failed block
    @staticmethod
    def _treat_failed_block(block: ParsingFailedBlock, bibtex_format: BibtexFormat) -> list[str]:
        if isinstance(block.raw, str):
            lines = len(block.raw.splitlines())
            parsing_failed_comment = PARSING_FAILED_COMMENT.format(n=lines)
            return [parsing_failed_comment.rstrip(), "\n", block.raw.rstrip(), "\n"]
        else:
            if isinstance(block, DuplicateBlockKeyBlock):
                print(f"Duplicate key block: previous block key is `{block.key}`.")
            else:
                print(f"The raw of the field block: {block} is None.")
            return []
