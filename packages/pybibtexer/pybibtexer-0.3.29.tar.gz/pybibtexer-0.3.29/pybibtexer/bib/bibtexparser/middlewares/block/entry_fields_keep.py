import copy

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class KeepFieldsInEntry(BlockMiddleware):
    """Keep the fields of an entry according to a custom list of field keys provided by user."""

    def __init__(self, entry_type: str, keep_field_keys: list[str], allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.entry_type = entry_type
        self.keep_field_keys = keep_field_keys

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if self.entry_type == entry.entry_type:
            keep_field_keys = copy.deepcopy(self.keep_field_keys)
            if ("editor" in entry) and ("author" not in entry) and ("author" in self.keep_field_keys):
                keep_field_keys.append("editor")

            delete_field_keys = [k for k in entry.fields_dict.keys() if k not in keep_field_keys]
            for key in delete_field_keys:
                del entry[key]
        return entry

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return "keep_fields_custom"
