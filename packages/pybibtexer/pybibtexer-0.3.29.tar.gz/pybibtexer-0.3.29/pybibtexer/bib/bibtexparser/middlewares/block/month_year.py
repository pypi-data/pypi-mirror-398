from pyadvtools.core.convert import convert_str_month_to_number_month

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class ConvertStrMonthToInt(BlockMiddleware):
    """Convert the field `month` value of an entry when it is str to int type if possible."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "month" in entry:
            entry["month"] = convert_str_month_to_number_month(entry["month"])
        return entry


class ExtractYear(BlockMiddleware):
    """Convert the field `month` value of an entry when it is str to int type if possible."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        year = entry["year"] if "year" in entry else ""
        if year:
            year_list = [i for j in year.split("/") for i in j.split("-")]
            year_list = sorted(set(year_list), key=len, reverse=True)
            entry["year"] = f"{year_list[0]}"
        return entry
