from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class ReplaceFieldKeyInEntry(BlockMiddleware):
    """Replace field key by user."""

    def __init__(
        self,
        entry_type: str,
        old_field_keys: list[str],
        new_field_keys: list[str],
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.entry_type = entry_type
        self.old_field_keys = old_field_keys
        self.new_field_keys = new_field_keys

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if self.entry_type == entry.entry_type:
            for old, new in zip(self.old_field_keys, self.new_field_keys, strict=True):
                if (old != new) and (old in entry):
                    entry[new] = entry[old]
                    del entry[old]
        return entry
