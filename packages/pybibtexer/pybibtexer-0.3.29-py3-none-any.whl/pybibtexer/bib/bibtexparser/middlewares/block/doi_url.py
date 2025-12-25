import re

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class SimplifyDoiInEntry(BlockMiddleware):
    """Simplify doi by delete `https://doi.org/` if existed."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "doi" in entry:
            entry["doi"] = re.sub(r"https*://doi.org/", "", entry["doi"])
        return entry


class ChooseDoiOrUrlInEntry(BlockMiddleware):
    """Choose doi when an item has both a doi and a url."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if ("doi" in entry) and (len(entry["doi"]) != 0) and ("url" in entry):
            del entry["url"]
        return entry


class ChangeDoiToUrlInEntry(BlockMiddleware):
    """Chang doi to url by add `https://doi.org/` if not existed, and then delete doi."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "doi" in entry:
            if len(doi := entry["doi"]) != 0:
                if not re.match(r"https*://", doi):
                    doi = f"https://doi.org/{doi}"
                entry["url"] = doi

            del entry["doi"]
        return entry


class HttpsUrlInEntry(BlockMiddleware):
    """Change http to https for security."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "url" in entry:
            entry["url"] = re.sub(r"https*://", "https://", entry["url"])
        return entry
