import re
from copy import deepcopy

from ...library import Library
from ...model import Block, Entry, ExplicitComment, ImplicitComment, ParsingFailedBlock, Preamble, String
from ..middleware import LibraryMiddleware

DEFAULT_BLOCK_TYPE_ORDER = (ImplicitComment, ExplicitComment, String, Preamble, Entry, ParsingFailedBlock, Block)


class SortBlocksByTypeAndUserSortKeyMiddleware(LibraryMiddleware):
    """Sorts the blocks of a library by type and `User Sort Key`."""

    def __init__(
        self,
        keep_entry_according_cite_keys: list[str] | None = None,
        sort_entry_according_field_keys: list[str] | None = None,
        sort_entry_according_field_keys_reverse: bool = True,
    ):
        if keep_entry_according_cite_keys is None:
            keep_entry_according_cite_keys = []
        if sort_entry_according_field_keys is None:
            sort_entry_according_field_keys = ["year", "volume", "number", "month", "pages"]

        self._verify_all_types_are_block_types(DEFAULT_BLOCK_TYPE_ORDER)
        self.keep_entry_according_cite_keys = keep_entry_according_cite_keys
        self.sort_entry_according_field_keys = sort_entry_according_field_keys
        self.sort_entry_according_field_keys_reverse = sort_entry_according_field_keys_reverse

        # In-place modification is not yet supported, we make this explicit here,
        super().__init__(allow_inplace_modification=False)

    @staticmethod
    def _verify_all_types_are_block_types(sort_order):
        for t in sort_order:
            if not issubclass(t, Block):
                raise ValueError(f"Sort order must only contain Block subclasses, but got {t}")

    # docstr-coverage: inherited
    def transform(self, library: Library) -> Library:
        library = super().transform(library)
        blocks = library.blocks

        _blocks = []

        _implicit_comments = [b for b in blocks if isinstance(b, ImplicitComment)]
        _implicit_comments = sorted(_implicit_comments, key=lambda x: len(x.comment), reverse=False)

        _explicit_comments = [b for b in blocks if isinstance(b, ExplicitComment)]
        _explicit_comments = sorted(_explicit_comments, key=lambda x: len(x.comment), reverse=False)

        _strings = sorted(library.strings, key=lambda x: x.key, reverse=False)

        _preambles = sorted(library.preambles, key=lambda x: len(x.value), reverse=False)

        _entries = library.entries
        if self.keep_entry_according_cite_keys:
            _entries = sorted(_entries, key=self._sort_entry_one, reverse=False)
        else:
            _entries = sorted(_entries, key=self._sort_entry_two, reverse=self.sort_entry_according_field_keys_reverse)

        _failed_blocks = deepcopy(library.failed_blocks)
        _failed_blocks = sorted(_failed_blocks, key=lambda x: len(x.__class__.__name__), reverse=False)

        _others = [
            b
            for b in blocks
            if not (
                isinstance(b, ImplicitComment)
                or isinstance(b, ExplicitComment)
                or isinstance(b, String)
                or isinstance(b, Preamble)
                or isinstance(b, Entry)
                or isinstance(b, ParsingFailedBlock)
            )
        ]
        _others = sorted(_others, key=lambda x: len(x.__class__.__name__), reverse=False)

        # order of blocks
        _blocks.extend(_strings)
        _blocks.extend(_entries)
        _blocks.extend(_preambles)
        _blocks.extend(_explicit_comments)
        _blocks.extend(_implicit_comments)
        _blocks.extend(_failed_blocks)
        _blocks.extend(_others)
        return Library(blocks=_blocks)

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return "sort_blocks_by_type_and_user_sort_key"

    def _sort_entry_one(self, entry):
        if entry.key in self.keep_entry_according_cite_keys:
            return self.keep_entry_according_cite_keys.index(entry.key)
        else:
            return -1

    def _sort_entry_two(self, entry):
        _sorting_index = []
        _sorting_index.append(entry.entry_type)
        for k in self.sort_entry_according_field_keys:
            if k in entry.fields_dict:
                v = entry.fields_dict[k].value
                # for sorting
                if k == "pages":
                    v = v.split("——")[0].split("--")[0].split("–")[0].split("-")[0]
                if k == "month":
                    v = v.split("–")[0].split("-")[0].split("/")[0]
                _sorting_index.append(v)
            else:
                _sorting_index.append("0")
        return self.sort_strings_with_embedded_numbers("_".join(_sorting_index))

    @staticmethod
    def sort_strings_with_embedded_numbers(s: str) -> list[str]:
        re_digits = re.compile(r"(\d+)")
        pieces = re_digits.split(s)
        pieces[1::2] = map(int, pieces[1::2])
        return pieces
