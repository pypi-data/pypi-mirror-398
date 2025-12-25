import re

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware
from ..utils import generate_cite_key_prefix


class AddArchive(BlockMiddleware):
    """Add Field `archive`."""

    def __init__(
        self,
        abbr_article_pattern_dict: dict,
        abbr_inproceedings_pattern_dict: dict,
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.abbr_article_pattern_dict = abbr_article_pattern_dict
        self.abbr_inproceedings_pattern_dict = abbr_inproceedings_pattern_dict

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        entry["archive"] = generate_cite_key_prefix(
            entry,
            self.abbr_article_pattern_dict,
            self.abbr_inproceedings_pattern_dict,
        )
        return entry


class AddJournalLongAbbr(BlockMiddleware):
    """Add long abbr for field `journal`."""

    def __init__(
        self,
        full_abbr_article_dict: dict,
        full_names_in_json: str,
        abbr_names_in_json: str,
        abbr_article_pattern_dict: dict,
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.full_abbr_article_dict = full_abbr_article_dict
        self.full_names_in_json = full_names_in_json
        self.abbr_names_in_json = abbr_names_in_json
        self.abbr_article_pattern_dict = abbr_article_pattern_dict
        self.abbr_inproceedings_pattern_dict = {}

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if entry.entry_type.lower() != "article":
            return entry

        prefix = generate_cite_key_prefix(entry, self.abbr_article_pattern_dict, self.abbr_inproceedings_pattern_dict)
        abbr = prefix.replace("J_", "")
        return self.generate_journal_booktitle_long_abbr(entry, abbr)

    def generate_journal_booktitle_long_abbr(self, entry: Entry, abbr: str) -> Entry:
        # Only for journal
        if entry.entry_type.lower() == "article":
            field_key = "journal"
            full_name_list = self.full_abbr_article_dict.get(abbr, {}).get(self.full_names_in_json, [])
            long_abbr_name_list = self.full_abbr_article_dict.get(abbr, {}).get(self.abbr_names_in_json, [])
        else:
            return entry

        field_content = entry[field_key] if field_key in entry else ""
        field_content = re.sub(r"\(.*\)", "", field_content).strip()

        if not field_content:
            return entry

        long_abbr_list = []
        for full, long_abbr in zip(full_name_list, long_abbr_name_list, strict=True):
            if re.match(f"^{full}", field_content, re.I):
                long_abbr_list.append(long_abbr)

        # check
        long_abbr_list = list(set(long_abbr_list))
        if len(long_abbr_list) > 1:
            print(f"Multiple match: {long_abbr_list} for {field_content}.")
        elif len(long_abbr_list) == 1:
            entry["shortjournal"] = long_abbr_list[0]
        return entry
