from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class ConstrainNumberOfAuthors(BlockMiddleware):
    """Constrain the number of authors."""

    def __init__(self, maximum_authors: int, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.maximum_authors = maximum_authors

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "author" in entry:
            authors = entry["author"].split(" and ")
            if len(authors) > self.maximum_authors:
                authors = authors[: self.maximum_authors]
                authors.append("others")
                entry["author"] = " and ".join(authors)
        return entry
