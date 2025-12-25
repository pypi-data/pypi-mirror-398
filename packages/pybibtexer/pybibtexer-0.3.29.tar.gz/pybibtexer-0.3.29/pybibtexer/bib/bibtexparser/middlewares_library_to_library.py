import copy
from typing import Any

from .library import Library
from .middlewares.block.add_field import AddArchive, AddJournalLongAbbr
from .middlewares.block.authors import ConstrainNumberOfAuthors
from .middlewares.block.doi_url import ChangeDoiToUrlInEntry, ChooseDoiOrUrlInEntry, HttpsUrlInEntry, SimplifyDoiInEntry
from .middlewares.block.entry_field_keys_normalize import NormalizeEntryFieldKeys
from .middlewares.block.entry_field_keys_replace import ReplaceFieldKeyInEntry
from .middlewares.block.entry_field_values_normalize import AddUrlToFieldValueInEntry, NormalizeFieldValuesInEntry
from .middlewares.block.entry_fields_delete import DeleteFieldsInEntry
from .middlewares.block.entry_fields_keep import KeepFieldsInEntry
from .middlewares.block.entry_fields_sort import SortFieldsAlphabeticallyMiddleware
from .middlewares.block.entry_types import NormalizeEntryTypes
from .middlewares.block.journal_booktitle import AbbreviateJournalBooktitle, DeleteRedundantInJournalBooktitle
from .middlewares.block.month_year import ConvertStrMonthToInt, ExtractYear
from .middlewares.block.number_volume import ConvertStrNumberVolumeToInt
from .middlewares.block.pages import NormalizePagesInEntry
from .middlewares.block.title import NormalizeTitleInEntry
from .middlewares.library.generating_entrykeys import GenerateEntriesCiteKey
from .middlewares.library.keeping_blocks import KeepEntriesByCiteKey
from .middlewares.library.protecting_title import ProtectTitleWithBracket
from .middlewares.library.sorting_blocks import SortBlocksByTypeAndUserSortKeyMiddleware

keep_entry_list = [
    "article",
    "inproceedings",
    "incollection",
    "misc",
    "book",
    "phdthesis",
    "mastersthesis",
    "techreport",
]
common_field_list = ["author", "title", "year", "month", "doi", "url", "annotation"]


def keep_for_abbr():
    keep_field_list_list_temp = [
        ["journal", "pages", "volume", "number"],  # 'article'
        ["booktitle", "pages"],  # 'inproceedings'
        ["booktitle", "pages", "publisher"],  # 'incollection'
        ["publisher", "howpublished", "pages"],  # 'misc'
        ["publisher", "edition"],  # 'book'
        ["type", "school", "address", "pages"],  # 'phdthesis'
        ["type", "school", "address", "pages"],  # 'mastersthesis'
        ["type", "institution", "address", "pages"],  # 'techreport'
    ]

    common_field_list_temp = []
    common_field_list_temp.extend(common_field_list)

    keep_field_list_list = []
    for i in keep_field_list_list_temp:
        i.extend(common_field_list_temp)
        keep_field_list_list.append(i)
    return keep_entry_list, keep_field_list_list


def keep_for_zotero():
    keep_field_list_list_temp = [
        ["journal", "pages", "volume", "number"],  # 'article'
        ["booktitle", "pages"],  # 'inproceedings'
        ["booktitle", "pages", "publisher"],  # 'incollection'
        ["publisher", "pages"],  # 'misc' (no howpublished)
        ["publisher", "edition"],  # 'book'
        ["type", "school", "address", "pages"],  # 'phdthesis'
        ["type", "school", "address", "pages"],  # 'mastersthesis'
        ["type", "institution", "address", "pages"],  # 'techreport'
    ]

    common_field_list_temp = ["abstract"]
    common_field_list_temp.extend(common_field_list)

    keep_field_list_list = []
    for i in keep_field_list_list_temp:
        i.extend(common_field_list_temp)
        keep_field_list_list.append(i)
    return keep_entry_list, keep_field_list_list


class MiddlewaresLibraryToLibrary:
    """Middlewares for converting a library to a library.

    Args:
        options (dict): Options for the middlewares.

    Attributes:
        function_common_again (bool): Run common middlewares again. Default is True.

        lower_entry_type (bool): Lower Entry type. Default is True.
        lower_entry_field_key (bool): Lower Entry field keys. Default is True.
        keep_entries_by_cite_keys (list): list of keys to keep entries in the order of cite keys. Default is [].
        update_month (bool): Convert str month to int month. Default is True.
        update_number_volume (bool): Update number and volume. Default is True.
        update_pages (bool): Update pages. Default is True.
        update_title (bool): Update title. Default is True.
        sentence_title_case (bool): Sentence title case. Default is True.
        generate_entry_cite_keys (bool): Generate Entry keys (cite keys). Default is False.
        full_abbr_article_dict (dict): Full to abbreviation dictionary for article. Default is {}.
        full_abbr_inproceedings_dict (dict): Full to abbreviation dictionary for inproceedings. Default is {}.
        full_names_in_json (str): Full names in json format. Default is "".
        abbr_names_in_json (str): Abbreviated names in json format. Default is "".
        abbr_article_pattern_dict (dict): Pre-compiled regex patterns for journal name matching
        abbr_inproceedings_pattern_dict (dict): Pre-compiled regex patterns for conference name matching

        full_to_abbr_for_abbr (bool): Full to abbreviation for abbreviate. Default is True.
        abbr_index_article_for_abbr (int): Index for abbreviation in article. Default is 1.
        abbr_index_inproceedings_for_abbr (int): Index for abbreviation in inproceedings. Default is 2.
        protect_title_with_bracket_for_abbr (bool): Protect title with bracket. Default is True
        doi_or_url_for_abbr (bool): Keep only doi or url. Default is True.
        doi_to_url_for_abbr (bool): Change doi to url and delete original doi. Default is True.
        add_link_to_fields_for_abbr (Optional[list[str]] = None): Add link to fields. Default is None.
        is_keep_fields_for_abbr (bool): Keep fields for abbreviate. Default is True.
        keep_entry_list_for_abbr (list): Entry list for keep fields. Default is keep_for_abbr()[0].
        keep_field_list_list_for_abbr (list): Field list list for keep fields. Default is keep_for_abbr()[1].
        delete_field_list_for_abbr (list): Delete fields list for abbreviate. Default is [].
        replace_fields_for_abbr (bool): Replace fields for abbreviate. Default is True.
        replace_old_field_list_for_abbr (list): Old field list for replace. Default is [["publisher"]].
        replace_new_field_list_for_abbr (list): New field list for replace. Default is [["howpublished"]].
        replace_entry_list_for_abbr (list): Entry list for replace. Default is ["misc"].
        maximum_authors_for_abbr (int): Maximum number of authors. Default is 0.

        protect_title_with_bracket_for_zotero (bool): Protect title with bracket. Default is False
        doi_or_url_for_zotero (bool): Keep only doi or url. Default is True.
        is_keep_fields_for_zotero (bool): Keep fields for zotero. Default is True.
        keep_entry_list_for_zotero (list): Entry list for keep fields. Default is keep_for_zotero()[0].
        keep_field_list_list_for_zotero (list): Field list list for keep fields. Default is keep_for_zotero()[1].
        delete_field_list_for_zotero (list): Delete fields list for zotero. Default is [].
        delete_redundant_in_journal_booktitle (bool): Delete redundant parts in journal and booktitle. Default is True.
        title_journal_booktitle_for_zotero (bool): Title journal and booktitle contents. Default is True.
        add_archive_for_zotero (bool): Add field 'archive'. Default is True.
        add_journal_abbr_for_zotero (bool): Add 'journal/booktitle abbreviation'. Default is True.

        protect_title_with_bracket_for_save (bool): Protect title with bracket. Default is False
        delete_field_list_for_save (list): Delete fields list for save. Default is [].

        is_sort_entry_fields (bool): Sort entry fields alphabetically. Default is True.
        is_sort_blocks (bool): Sort entries by type and user sort key. Default is True.
        sort_entries_by_cite_keys (list): list of keys to sort entries in the order of cite keys. Default is [].
        sort_entries_by_field_keys (list): list of keys to sort entries in the order of field keys. Default is
            ["year", "volume", "number", "month", "pages"].
        sort_entries_by_field_keys_reverse (bool): Reverse the sorting of the field keys. Default is True.

    """

    def __init__(self, options: dict[str, Any]):
        self.function_common_again = options.get("function_common_again", True)
        self.function_common_again_for_abbr = options.get("function_common_again_for_abbr", True)
        self.function_common_again_for_zotero = options.get("function_common_again_for_zotero", True)
        self.function_common_again_for_save = options.get("function_common_again_for_save", True)
        self._initialize_function_sort(options)

        self._initialize_function_common(options)
        self._initialize_function_abbr(options)
        self._initialize_function_zotero(options)
        self._initialize_function_save(options)

    def functions(self, library: Library) -> tuple[Library, Library, Library]:
        if self.function_common_again:
            library = self._function_common(library)

        abbr_library = self._function_abbr(copy.deepcopy(library))
        zotero_library = self._function_zotero(copy.deepcopy(library))
        save_library = self._function_save(copy.deepcopy(library))
        return abbr_library, zotero_library, save_library

    def function_abbr(self, library: Library) -> Library:
        if self.function_common_again_for_abbr:
            library = self._function_common(library)
        return self._function_abbr(library)

    def function_zotero(self, library: Library) -> Library:
        if self.function_common_again_for_zotero:
            library = self._function_common(library)
        return self._function_zotero(library)

    def function_save(self, library: Library) -> Library:
        if self.function_common_again_for_save:
            library = self._function_common(library)
        return self._function_save(library)

    def _initialize_function_common(self, options: dict[str, Any]) -> None:
        self.lower_entry_type = options.get("lower_entry_type", True)
        self.lower_entry_field_key = options.get("lower_entry_field_key", True)
        self.keep_entries_by_cite_keys = options.get("keep_entries_by_cite_keys", [])
        self.update_month_year = options.get("update_month_year", True)
        self.update_number_volume = options.get("update_number_volume", True)
        self.update_pages = options.get("update_pages", True)
        self.update_title = options.get("update_title", True)
        self.sentence_title_case = options.get("sentence_title_case", True)

        self.generate_entry_cite_keys = options.get("generate_entry_cite_keys", False)
        self.full_abbr_article_dict = options.get("full_abbr_article_dict", {})
        self.full_abbr_inproceedings_dict = options.get("full_abbr_inproceedings_dict", {})
        self.full_names_in_json = options.get("full_names_in_json", "")
        self.abbr_names_in_json = options.get("abbr_names_in_json", "")
        self.abbr_article_pattern_dict = options.get("abbr_article_pattern_dict", {})
        self.abbr_inproceedings_pattern_dict = options.get("abbr_inproceedings_pattern_dict", {})

    def _function_common(self, library: Library) -> Library:
        # Lower Entry types
        if self.lower_entry_type:
            library = NormalizeEntryTypes().transform(library)

        # Lower Entry Field keys
        if self.lower_entry_field_key:
            library = NormalizeEntryFieldKeys().transform(library)

        # Keep entries according to cite key
        if self.keep_entries_by_cite_keys:
            library = KeepEntriesByCiteKey(self.keep_entries_by_cite_keys).transform(library)

        # Convert str month to int month ("Feb" to "2")
        if self.update_month_year:
            library = ConvertStrMonthToInt().transform(library)
            library = ExtractYear().transform(library)

        # Update number and volume
        if self.update_number_volume:
            library = ConvertStrNumberVolumeToInt().transform(library)

        # Update pages
        if self.update_pages:
            library = NormalizePagesInEntry().transform(library)

        # Update doi
        library = SimplifyDoiInEntry().transform(library)

        # Update url
        library = HttpsUrlInEntry().transform(library)

        # Update title (by deleting \href{}{})
        if self.update_title:
            library = NormalizeTitleInEntry().transform(library)

        # Must set before self.add_link_to_fields_for_abbr
        if self.sentence_title_case:
            library = NormalizeFieldValuesInEntry("title", "sentence").transform(library)

        # Generate Entry keys (cite keys)
        if self.generate_entry_cite_keys:
            library = GenerateEntriesCiteKey(
                self.abbr_article_pattern_dict,
                self.abbr_inproceedings_pattern_dict,
            ).transform(library)
        return library

    def _initialize_function_abbr(self, options: dict[str, Any]) -> None:
        self.full_to_abbr_for_abbr = options.get("full_to_abbr_for_abbr", True)
        self.abbr_index_article_for_abbr = options.get("abbr_index_article_for_abbr", 1)  # 0, 1, 2
        self.abbr_index_inproceedings_for_abbr = options.get("abbr_index_inproceedings_for_abbr", 2)  # 0, 1, 2

        self.protect_title_with_bracket_for_abbr = options.get("protect_title_with_bracket_for_abbr", True)

        self.doi_or_url_for_abbr = options.get("doi_or_url_for_abbr", True)  # keep only doi or url
        self.doi_to_url_for_abbr = options.get("doi_to_url_for_abbr", True)  # change (https://doi.org/xxx) to doi
        self.add_link_to_fields_for_abbr = options.get("add_link_to_fields_for_abbr", None)  # add link to fields

        self.is_keep_fields_for_abbr = options.get("is_keep_fields_for_abbr", True)
        self.keep_entry_list_for_abbr = options.get("keep_entry_list_for_abbr", keep_for_abbr()[0])
        self.keep_field_list_list_for_abbr = options.get("keep_field_list_list_for_abbr", keep_for_abbr()[1])

        self.delete_field_list_for_abbr = options.get("delete_field_list_for_abbr", [])

        self.replace_fields_for_abbr = options.get("replace_fields_for_abbr", True)
        self.replace_old_field_list_for_abbr = options.get("replace_old_field_list_for_abbr", [["publisher"]])
        self.replace_new_field_list_for_abbr = options.get("replace_new_field_list_for_abbr", [["howpublished"]])
        self.replace_entry_list_for_abbr = options.get("replace_entry_list_for_abbr", ["misc"])

        self.maximum_authors_for_abbr = options.get("maximum_authors_for_abbr", 0)

    def _function_abbr(self, library: Library) -> Library:
        # abbreviate
        if self.full_to_abbr_for_abbr:
            library = AbbreviateJournalBooktitle(
                self.full_abbr_article_dict,
                self.full_abbr_inproceedings_dict,
                self.abbr_index_article_for_abbr,
                self.abbr_index_inproceedings_for_abbr,
                self.full_names_in_json,
                self.abbr_names_in_json,
                self.abbr_article_pattern_dict,
                self.abbr_inproceedings_pattern_dict,
            ).transform(library)

        # Protect title
        if self.protect_title_with_bracket_for_abbr:
            library = ProtectTitleWithBracket().transform(library)

        # Just keep doi or url (doi > url)
        if self.doi_or_url_for_abbr:
            library = ChooseDoiOrUrlInEntry().transform(library)

        # Change doi to url and delete original doi
        if self.doi_to_url_for_abbr:
            library = ChangeDoiToUrlInEntry().transform(library)

        # Add link to field content
        if self.add_link_to_fields_for_abbr is not None:
            for field in self.add_link_to_fields_for_abbr:
                library = AddUrlToFieldValueInEntry(field).transform(library)

        # Must set after self.add_link_to_title_for_abbr
        if self.is_keep_fields_for_abbr:
            for i, j in zip(self.keep_entry_list_for_abbr, self.keep_field_list_list_for_abbr, strict=True):
                library = KeepFieldsInEntry(i, j).transform(library)

        # Delete some fields for all entrys
        if self.delete_field_list_for_abbr:
            library = DeleteFieldsInEntry(self.delete_field_list_for_abbr).transform(library)

        # Replace some fields for all entrys
        if self.replace_fields_for_abbr:
            for entry in self.replace_entry_list_for_abbr:
                for old, new in zip(
                    self.replace_old_field_list_for_abbr, self.replace_new_field_list_for_abbr, strict=True
                ):
                    library = ReplaceFieldKeyInEntry(entry, old, new).transform(library)

        # Constrain the number of authors
        if self.maximum_authors_for_abbr:
            library = ConstrainNumberOfAuthors(self.maximum_authors_for_abbr).transform(library)

        library = self._function_sort(library)
        return library

    def _initialize_function_zotero(self, options: dict[str, Any]) -> None:
        self.protect_title_with_bracket_for_zotero = options.get("protect_title_with_bracket_for_zotero", False)

        self.doi_or_url_for_zotero = options.get("doi_or_url_for_zotero", True)  # keep only doi or url

        self.is_keep_fields_for_zotero = options.get("is_keep_fields_for_zotero", True)
        self.keep_entry_list_for_zotero = options.get("keep_entry_list_for_zotero", keep_for_zotero()[0])
        self.keep_field_list_list_for_zotero = options.get("keep_field_list_list_for_zotero", keep_for_zotero()[1])

        self.delete_field_list_for_zotero = options.get("delete_field_list_for_zotero", [])

        self.delete_redundant_in_journal_booktitle = options.get("delete_redundant_in_journal_booktitle", True)

        self.title_journal_booktitle_for_zotero = options.get("title_journal_booktitle_for_zotero", True)

        self.add_archive_for_zotero = options.get("add_archive_for_zotero", True)
        self.add_journal_abbr_for_zotero = options.get("add_journal_abbr_for_zotero", True)

    def _function_zotero(self, library: Library) -> Library:
        # Protect title
        if self.protect_title_with_bracket_for_zotero:
            library = ProtectTitleWithBracket().transform(library)

        # Just keep doi or url (doi > url)
        if self.doi_or_url_for_zotero:
            library = ChooseDoiOrUrlInEntry().transform(library)

        # Must set after self.add_link_to_title_for_abbr
        if self.is_keep_fields_for_zotero:
            for i, j in zip(self.keep_entry_list_for_zotero, self.keep_field_list_list_for_zotero, strict=True):
                library = KeepFieldsInEntry(i, j).transform(library)

        # Delete some fields for all entrys
        if self.delete_field_list_for_zotero:
            library = DeleteFieldsInEntry(self.delete_field_list_for_zotero).transform(library)

        # Delete redundant parts in journal and booktitle such as `CEC`
        if self.delete_redundant_in_journal_booktitle:
            library = DeleteRedundantInJournalBooktitle().transform(library)

        # Title `journal` and `booktitle` contents
        if self.title_journal_booktitle_for_zotero:
            library = NormalizeFieldValuesInEntry("journal", "title").transform(library)
            library = NormalizeFieldValuesInEntry("booktitle", "title").transform(library)

        # Add field 'archive'
        if self.add_archive_for_zotero:
            library = AddArchive(
                self.abbr_article_pattern_dict,
                self.abbr_inproceedings_pattern_dict,
            ).transform(library)

        # Add field 'journal abbreviation'
        if self.add_journal_abbr_for_zotero:
            library = AddJournalLongAbbr(
                self.full_abbr_article_dict,
                self.full_names_in_json,
                self.abbr_names_in_json,
                self.abbr_article_pattern_dict,
            ).transform(library)

        library = self._function_sort(library)
        return library

    def _initialize_function_save(self, options: dict[str, Any]) -> None:
        self.protect_title_with_bracket_for_save = options.get("protect_title_with_bracket_for_save", False)

        self.delete_field_list_for_save = options.get("delete_field_list_for_save", [])

    def _function_save(self, library: Library) -> Library:
        # Protect title
        if self.protect_title_with_bracket_for_save:
            library = ProtectTitleWithBracket().transform(library)

        # Delete some fields for all entrys
        if self.delete_field_list_for_save:
            library = DeleteFieldsInEntry(self.delete_field_list_for_save).transform(library)

        library = self._function_sort(library)
        return library

    def _initialize_function_sort(self, options: dict[str, Any]) -> None:
        self.is_sort_entry_fields = options.get("is_sort_entry_fields", False)
        self.is_sort_blocks = options.get("is_sort_blocks", False)
        self.sort_entries_by_cite_keys = options.get("sort_entries_by_cite_keys", [])
        self.sort_entries_by_field_keys = options.get(
            "sort_entries_by_field_keys", ["year", "volume", "number", "month", "pages"]
        )
        self.sort_entries_by_field_keys_reverse = options.get("sort_entries_by_field_keys_reverse", False)

    def _function_sort(self, library: Library) -> Library:
        # Sort fields alphabetically
        if self.is_sort_entry_fields:
            library = SortFieldsAlphabeticallyMiddleware().transform(library)

        # Sort blocks by type and user sort key
        if self.is_sort_blocks:
            library = SortBlocksByTypeAndUserSortKeyMiddleware(
                self.sort_entries_by_cite_keys, self.sort_entries_by_field_keys, self.sort_entries_by_field_keys_reverse
            ).transform(library)
        return library
