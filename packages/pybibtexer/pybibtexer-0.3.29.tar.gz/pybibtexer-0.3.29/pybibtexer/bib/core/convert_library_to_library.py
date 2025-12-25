from typing import Any

from ..bibtexparser import Library, MiddlewaresLibraryToLibrary


class ConvertLibrayToLibrary:
    """Convert library to library.

    Args:
        options (dict[str, Any]): Options. Default is {}.

    Attributes:
        choose_abbr_zotero_save (str): Choose "abbr", "zotero", or "save". Default is "save".
    """

    def __init__(self, options: dict[str, Any] = {}) -> None:
        self.choose_abbr_zotero_save = options.get("choose_abbr_zotero_save", "save")

        self._middleware_library_library = MiddlewaresLibraryToLibrary(options)

    def generate_single_library(self, library: Library, given_cite_keys: list[str] | None = None) -> Library:
        if given_cite_keys is None:
            given_cite_keys = []

        library = self._update_library_by_entry_keys(library, given_cite_keys)

        func = eval(f"_x.function_{self.choose_abbr_zotero_save}", {}, {"_x": self._middleware_library_library})
        library = func(library)

        return library

    def generate_multi_libraries(
        self, library: Library, given_cite_keys: list[str] | None = None
    ) -> tuple[Library, Library, Library]:
        if given_cite_keys is None:
            given_cite_keys = []

        library = self._update_library_by_entry_keys(library, given_cite_keys)

        abbr_library, zotero_library, save_library = self._middleware_library_library.functions(library)

        return abbr_library, zotero_library, save_library

    @staticmethod
    def _update_library_by_entry_keys(library: Library, keys: list[str]):
        if len(keys) == 0:
            return library

        for entry in library.entries:
            if entry.key not in keys:
                library.remove(entry)

        return library
