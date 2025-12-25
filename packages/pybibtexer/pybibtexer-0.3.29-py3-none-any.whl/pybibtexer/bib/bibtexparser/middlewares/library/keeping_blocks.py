from ...library import Library
from ..middleware import LibraryMiddleware


class KeepEntriesByCiteKey(LibraryMiddleware):
    """Keep the entries of a library by `Cite Key`.

    The entry.key is also `Cite Key`.
    """

    def __init__(self, entry_keys: list[str], allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.entry_keys = [e.lower() for e in entry_keys]

    # docstr-coverage: inherited
    def transform(self, library: Library) -> Library:
        library = super().transform(library)
        for entry in library.entries:
            if entry.key.lower() not in self.entry_keys:
                library.remove(entry)
        return library

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return "keep_entry_according_cite_keys"
