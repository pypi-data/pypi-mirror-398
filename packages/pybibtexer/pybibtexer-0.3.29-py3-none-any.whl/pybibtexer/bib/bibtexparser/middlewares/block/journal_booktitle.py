import re

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware
from ..utils import generate_cite_key_prefix


class AbbreviateJournalBooktitle(BlockMiddleware):
    """Abbreviate the field `journal` or `booktitle` value of an entry."""

    def __init__(
        self,
        full_abbr_article_dict: dict,
        full_abbr_inproceedings_dict: dict,
        abbr_index_article_for_abbr: int,
        abbr_index_inproceedings_for_abbr: int,
        full_names_in_json: str,
        abbr_names_in_json: str,
        abbr_article_pattern_dict: dict,
        abbr_inproceedings_pattern_dict: dict,
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.full_abbr_article_dict = full_abbr_article_dict
        self.full_abbr_inproceedings_dict = full_abbr_inproceedings_dict
        self.abbr_index_article_for_abbr = abbr_index_article_for_abbr
        self.abbr_index_inproceedings_for_abbr = abbr_index_inproceedings_for_abbr
        self.full_names_in_json = full_names_in_json
        self.abbr_names_in_json = abbr_names_in_json
        self.abbr_article_pattern_dict = abbr_article_pattern_dict
        self.abbr_inproceedings_pattern_dict = abbr_inproceedings_pattern_dict

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if entry.entry_type.lower() not in ["article", "inproceedings"]:
            return entry

        prefix = generate_cite_key_prefix(entry, self.abbr_article_pattern_dict, self.abbr_inproceedings_pattern_dict)
        abbr = prefix.replace("J_", "").replace("C_", "")
        return self.abbreviate_journal_booktitle(entry, abbr)

    def abbreviate_journal_booktitle(self, entry: Entry, abbr: str) -> Entry:
        """Abbreviate."""
        if entry.entry_type.lower() == "article":
            field_key = "journal"
            abbr_index = self.abbr_index_article_for_abbr
            full_name_list = self.full_abbr_article_dict.get(abbr, {}).get(self.full_names_in_json, [])
            long_abbr_name_list = self.full_abbr_article_dict.get(abbr, {}).get(self.abbr_names_in_json, [])
        elif entry.entry_type.lower() == "inproceedings":
            field_key = "booktitle"
            abbr_index = self.abbr_index_inproceedings_for_abbr
            full_name_list = self.full_abbr_inproceedings_dict.get(abbr, {}).get(self.full_names_in_json, [])
            long_abbr_name_list = self.full_abbr_inproceedings_dict.get(abbr, {}).get(self.abbr_names_in_json, [])
        else:
            return entry

        if abbr_index not in [1, 2]:
            return entry

        # Case 1
        if abbr_index == 2:
            entry[field_key] = abbr
            return entry

        # Case 2
        field_content = entry[field_key] if field_key in entry else ""
        field_content = re.sub(r"\(.*\)", "", field_content).strip()

        if not field_content:
            return entry

        # match
        content_list = []
        if abbr_index == 1:
            for full, long_abbr in zip(full_name_list, long_abbr_name_list, strict=True):
                if re.match(f"^{full}$", field_content, re.I):
                    content_list.append(long_abbr)

        # check
        content_list = list(set(content_list))
        if len(content_list) > 1:
            print(f"Multiple match: {content_list} for {field_content}.")
        elif len(content_list) == 1:
            entry[field_key] = content_list[0]
        return entry


class DeleteRedundantInJournalBooktitle(BlockMiddleware):
    """Delete redundant part such as `(CEC)` in field `journal` or `booktitle` value of an entry."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if entry.entry_type.lower() in ["article", "inproceedings"]:
            for i in ["journal", "booktitle"]:
                value = entry[i] if i in entry else ""
                if value:
                    entry[i] = re.sub(r"\(.*\)", "", value).strip()
        return entry
