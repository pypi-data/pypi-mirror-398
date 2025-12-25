import re

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class NormalizeTitleInEntry(BlockMiddleware):
    r"""Normalize field `title` of an entry by deleting \href{}{} if existed."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        regex = re.compile(r"\\href{(.*)}{(.*)}")
        if "title" in entry:
            if mch := regex.search(entry["title"]):
                entry["title"] = mch.group(2)
        return entry
