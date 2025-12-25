from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class ConvertStrNumberVolumeToInt(BlockMiddleware):
    """Convert the field `number` or `volume` value of an entry when it is str to int type if possible."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        for i in ["number", "volume"]:
            value = entry[i] if i in entry else ""
            if value:
                try:
                    entry[i] = f"{int(value)}"
                except ValueError:
                    pass
        return entry
