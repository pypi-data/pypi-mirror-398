from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class NormalizeEntryTypes(BlockMiddleware):
    """Normalize Entry types."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        entry.entry_type = entry.entry_type.lower()
        return entry
