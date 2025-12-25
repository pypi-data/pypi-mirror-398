from typing import Any

from .middlewares.block.entry_fields_sort import SortFieldsAlphabeticallyMiddleware
from .middlewares.library.sorting_blocks import SortBlocksByTypeAndUserSortKeyMiddleware


class MiddlewaresLibraryToStr:
    """Middlewares for converting a library to a string.

    Args:
        options (dict): Options for the middlewares.

    Attributes:
        is_sort_entry_fields (bool): Sort entry fields alphabetically. Default is True.
        is_sort_blocks (bool): Sort entries by type and user sort key. Default is True.
        sort_entries_by_cite_keys (list): list of keys to sort entries in the order of cite keys. Default is [].
        sort_entries_by_field_keys (list): list of keys to sort entries in the order of field keys. Default is
            ["year", "volume", "number", "month", "pages"].
        sort_entries_by_field_keys_reverse (bool): Reverse the sorting of the field keys. Default is True.
    """

    def __init__(self, options: dict[str, Any]):
        self.is_sort_entry_fields = options.get("is_sort_entry_fields", True)
        self.is_sort_blocks = options.get("is_sort_blocks", True)
        self.sort_entries_by_cite_keys = options.get("sort_entries_by_cite_keys", [])
        self.sort_entries_by_field_keys = options.get(
            "sort_entries_by_field_keys", ["year", "volume", "number", "month", "pages"]
        )
        self.sort_entries_by_field_keys_reverse = options.get("sort_entries_by_field_keys_reverse", True)

    def functions(self, library):
        # Sort fields alphabetically
        if self.is_sort_entry_fields:
            library = SortFieldsAlphabeticallyMiddleware().transform(library)

        # Sort blocks by type and user sort key
        if self.is_sort_blocks:
            library = SortBlocksByTypeAndUserSortKeyMiddleware(
                self.sort_entries_by_cite_keys, self.sort_entries_by_field_keys, self.sort_entries_by_field_keys_reverse
            ).transform(library)

        return library
