from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class DeleteFieldsInEntry(BlockMiddleware):
    """Delete fields by user."""

    def __init__(
        self, delete_field_keys: list[str], entry_type: str | None = None, allow_inplace_modification: bool = True
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.entry_type = entry_type
        self.delete_field_keys = delete_field_keys

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if self.entry_type is None:
            entry_type = entry.entry_type
        else:
            entry_type = self.entry_type

        if entry_type == entry.entry_type:
            for key in self.delete_field_keys:
                del entry[key]
        return entry

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return "delete_custom_fields"
