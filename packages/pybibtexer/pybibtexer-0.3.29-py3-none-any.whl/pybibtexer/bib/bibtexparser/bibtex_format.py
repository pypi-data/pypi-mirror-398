PARSING_FAILED_COMMENT = "% WARNING Parsing failed for the following {n} lines."


class BibtexFormat:
    """Definition of formatting (alignment, ...) when writing a BibTeX file.

    Hint: For more manual, GUI-based formatting, see the `bibtex-tidy` tool:
        https://flamingtempura.github.io/bibtex-tidy/
    """

    def __init__(self):
        self._indent: str = "  "  # "\t"
        self._align_field_values: int | str = "auto"
        self._block_separator: str = ""  # "\n\n"
        self._trailing_comma: bool = True
        self._parsing_failed_comment: str = PARSING_FAILED_COMMENT

    @property
    def indent(self) -> str:
        """Character(s) for indenting BibTeX field-value pairs. Default: single space."""
        return self._indent

    @indent.setter
    def indent(self, indent: str) -> None:
        self._indent = indent

    @property
    def value_column(self) -> int | str:
        """Controls the alignment of field- and string-values. Default: no alignment.

        This impacts String and Entry blocks.

        An integer value x specifies that spaces should be added before the " = ",
        such that, if possible, the value is written at column `len(self.indent) + x`.
        Note that for long keys, the value may be written at a later column.

        Thus, a value of 0 means that the value is written directly after the " = ".

        The special value "auto" specifies that the bibtex field value should be aligned
        based on the longest key in the library.
        """
        return self._align_field_values

    @value_column.setter
    def value_column(self, align_values: int | str) -> None:
        if isinstance(align_values, int):
            if align_values < 0:
                raise ValueError("align_field_values must be >= 0")
        elif align_values != "auto":
            raise ValueError("align_field_values must be an integer or 'auto'")
        self._align_field_values = align_values

    @property
    def block_separator(self) -> str:
        """Character(s) for separating BibTeX entries.

        Default: Two lines breaks, i.e., two blank lines.
        """
        return self._block_separator

    @block_separator.setter
    def block_separator(self, entry_separator: str) -> None:
        self._block_separator = entry_separator

    @property
    def trailing_comma(self) -> bool:
        """Use the trailing comma syntax for BibTeX entries. Default: True.

        BibTeX syntax allows an optional comma at the end
        of the last field in an entry.
        """
        return self._trailing_comma

    @trailing_comma.setter
    def trailing_comma(self, trailing_comma: bool) -> None:
        self._trailing_comma = trailing_comma

    @property
    def parsing_failed_comment(self) -> str:
        """Comment to use for blocks that could not be parsed."""
        return self._parsing_failed_comment

    @parsing_failed_comment.setter
    def parsing_failed_comment(self, parsing_failed_comment: str) -> None:
        self._parsing_failed_comment = parsing_failed_comment
