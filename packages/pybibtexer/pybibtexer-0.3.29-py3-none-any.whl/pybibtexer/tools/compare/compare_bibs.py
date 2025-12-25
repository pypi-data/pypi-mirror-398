import copy
import os
import re
from typing import Any

from pyadvtools import standard_path, transform_to_data_list

from ...bib.bibtexparser import Block, Library
from ...main import PythonRunBib, PythonWriters
from ..experiments_base import obtain_local_abbr_paths

ARXIV_BIORXIV = ["arxiv", "biorxiv", "ssrn"]


def obtain_local_abbr_paths_for_abbr(options: dict, path_spidered_bibs: str, path_spidering_bibs: str) -> list[str]:
    path_spidered_bibs = standard_path(path_spidered_bibs)
    path_spidering_bibs = standard_path(path_spidering_bibs)

    path_abbrs = []
    path_abbrs.extend(obtain_local_abbr_paths(os.path.join(path_spidered_bibs, "Journals"), options))
    path_abbrs.extend(obtain_local_abbr_paths(os.path.join(path_spidered_bibs, "Conferences"), options))
    path_abbrs.extend(obtain_local_abbr_paths(os.path.join(path_spidering_bibs, "spider_j"), options))
    path_abbrs.extend(obtain_local_abbr_paths(os.path.join(path_spidering_bibs, "spider_c"), options))

    if options.get("include_early_access", True):
        path_abbrs.extend(obtain_local_abbr_paths(os.path.join(path_spidering_bibs, "spider_j_e"), options))

    path_abbrs = [p for p in path_abbrs if os.path.basename(p).lower() not in ARXIV_BIORXIV]
    return path_abbrs


def compare_bibs_with_local(
    original_data: list[str] | str,
    path_spidered_bibs: str,
    path_spidering_bibs: str,
    path_output: str,
    options: dict[str, Any],
) -> None:
    """Compare bibliography entries with local bibliography collections.

    Processes original bibliography data and compares it against local bib files,
    categorizing entries into found, not found, and duplicate categories.
    Results are written to separate output files.

    Args:
        original_data: Input bibliography data as string or list of strings
        path_spidered_bibs: Path to pre-collected/spidered bibliography files
        path_spidering_bibs: Path to actively spidered bibliography files
        path_output: Output directory for result files
        options: Configuration options for comparison behavior

            compare_each_entry_with_all_local_bibs: Whether to compare each Entry with all local bib files.
    """
    path_output = standard_path(path_output)

    # generate for original data
    _options = {}
    _options.update(options)
    _python_bib = PythonRunBib(_options)
    data_list = transform_to_data_list(original_data, ".bib")
    library = _python_bib.parse_to_single_standard_library(data_list)
    original_entry_keys = [entry.key for entry in library.entries]

    # generate dict for abbr key entry
    if options.get("compare_each_entry_with_all_local_bibs"):
        abbr_key_entries_dict: dict[str, dict[str, Block]] = {"arXiv": {entry.key: entry for entry in library.entries}}
        not_in_local_entries = []
    else:
        abbr_key_entries_dict, not_in_local_entries = generate_abbr_key_entry_dict(library, options)

    # compare with local bibs
    tuple_entries = _compare_with_local(abbr_key_entries_dict, path_spidered_bibs, path_spidering_bibs, options)
    searched_entries, not_searched_entries, duplicate_original_entries, duplicate_searched_entries = tuple_entries
    not_in_local_entries.extend(not_searched_entries)

    # write with sorting blocks according to original cite keys
    _options = {}
    _options["is_sort_entry_fields"] = True  # default is True
    _options["is_sort_blocks"] = True  # default is True
    _options["sort_entries_by_cite_keys"] = original_entry_keys
    _python_write = PythonWriters(_options)
    _python_write.write_to_file(searched_entries, "in_local_entries.bib", "w", path_output, False)
    _python_write.write_to_file(not_in_local_entries, "not_in_local_entries.bib", "w", path_output, False)

    # write without sorting blocks
    _options = {}
    _options["is_sort_entry_fields"] = True  # default is True
    _options["is_sort_blocks"] = False  # default is True
    _python_write = PythonWriters(_options)
    _python_write.write_to_file(duplicate_original_entries, "duplicate_original_entries.bib", "w", path_output, False)
    _python_write.write_to_file(duplicate_searched_entries, "duplicate_searched_entries.bib", "w", path_output, False)
    return None


def generate_abbr_key_entry_dict(library: Library, options: dict[str, Any]):
    _options = {}
    _options["is_standardize_bib"] = True  # default is True
    _options["choose_abbr_zotero_save"] = "save"  # default is "save"
    _options["function_common_again"] = True  # default is True
    _options["generate_entry_cite_keys"] = True  # default is False
    _options.update(options)
    _python_bib = PythonRunBib(_options)

    abbr_key_entries_dict, not_in_local_entries = {}, []
    for entry in library.entries:
        flag = False

        if ("title" in entry) and (entry["title"].strip()) and ("year" in entry) and (entry["year"].strip()):
            temp_library = _python_bib.parse_to_single_standard_library(copy.deepcopy(Library([entry])))
            if len(entries := temp_library.entries) == 1:
                # article and inproceedings
                temps = entries[0].key.split("_")
                if (len(temps) == 3) and temps[0].lower() in ["j", "c"]:
                    abbr_key_entries_dict.setdefault(temps[1], {}).update({entry.key: entry})
                    flag = True

                # misc (arXiv, bioRxiv, and ssrn)
                elif (len(temps) == 2) and temps[0].lower() in ARXIV_BIORXIV:
                    abbr_key_entries_dict.setdefault("arXiv", {}).update({entry.key: entry})
                    flag = True

        if not flag:
            not_in_local_entries.append(entry)
    return abbr_key_entries_dict, not_in_local_entries


def _compare_with_local(
    abbr_key_entries_dict: dict[str, dict[str, Block]],
    local_path_spidered_bibs: str,
    local_path_spidering_bibs: str,
    options: dict[str, Any],
) -> tuple[list[Block], list[Block], list[Block], list[Block]]:
    # compare with local bibs
    searched_entries, not_searched_entries, duplicate_original_entries, duplicate_searched_entries = [], [], [], []
    for abbr, old_key_entries_dict in abbr_key_entries_dict.items():
        options_ = {}
        options_.update(options)
        if abbr.lower() not in ARXIV_BIORXIV:
            options_["include_abbr_list"] = [abbr]
        path_abbrs = obtain_local_abbr_paths_for_abbr(options_, local_path_spidered_bibs, local_path_spidering_bibs)

        new_key_entries_dict = {}
        for path_abbr in path_abbrs:
            if len(data_list := transform_to_data_list(path_abbr, ".bib")) == 0:
                continue

            print("*" * 9 + f" Compare in {f'{os.sep}'.join(path_abbr.split(os.sep)[-3:])} for {abbr} " + "*" * 9)

            _options = {}
            _options["is_standardize_bib"] = False  # default is True
            _options["choose_abbr_zotero_save"] = "save"  # default is "save"
            _options["function_common_again"] = False  # default is True
            _options["function_common_again_abbr"] = False  # default is True
            _options["function_common_again_zotero"] = False  # default is True
            _options["function_common_again_save"] = False  # default is True
            _options["generate_entry_cite_keys"] = False  # default is False
            _options.update(options)
            _library = PythonRunBib(_options).parse_to_single_standard_library(data_list)
            for key, entry in old_key_entries_dict.items():
                for _entry in _library.entries:
                    if check_equal_for_entry(entry, _entry, ["title"], abbr):
                        new_key_entries_dict.setdefault(key, []).append(copy.deepcopy(_entry))

        print()

        for key, entry in old_key_entries_dict.items():
            entries = new_key_entries_dict.get(key, [])
            if (length := len(entries)) == 1:
                entries[0].key = key
                searched_entries.extend(entries)
            elif length == 0:
                not_searched_entries.append(entry)
            else:
                for i, _entry in enumerate(entries):
                    _entry.key = key + "-a" * i
                duplicate_original_entries.append(entry)
                duplicate_searched_entries.extend(entries)

    return searched_entries, not_searched_entries, duplicate_original_entries, duplicate_searched_entries


def check_equal_for_entry(original_entry, new_entry, compare_field_list: list[str], abbr: str | None = None):
    a_list, b_list = [original_entry.entry_type.lower()], [new_entry.entry_type.lower()]
    if (abbr is not None) and (abbr.lower() in ARXIV_BIORXIV):
        a_list, b_list = [], []

    regex_title = re.compile(r"\\href{(.*)}{(.*)}")
    for field in compare_field_list:
        x = original_entry[field].lower().strip() if field in original_entry else ""
        y = new_entry[field].lower().strip() if field in new_entry else ""

        if field == "title":
            if mch := regex_title.search(x):
                x = mch.group(2)
            if mch := regex_title.search(y):
                y = mch.group(2)

        a_list.append(x)
        b_list.append(y)

    a_list = [re.sub(r"\W", "", a) for a in a_list]
    b_list = [re.sub(r"\W", "", b) for b in b_list]
    if "_".join(a_list) == "_".join(b_list):
        return True
    return False


def compare_bibs_with_zotero(
    zotero_bib: list[str] | str, download_bib: list[str] | str, path_output: str, options: dict[str, Any]
) -> None:
    """Compare downloaded bibliography entries with Zotero library entries.

    Processes both Zotero export and downloaded bibliography files, then compares
    them to identify entries that exist only in the download set versus entries
    that exist in both collections.

    Args:
        zotero_bib: Zotero exported bibliography data as string or list of strings
        download_bib: Downloaded bibliography data as string or list of strings
        path_output: Output directory path for result files
        options: Configuration options for parsing and comparison behavior
    """
    path_output = standard_path(path_output)

    # for zotero bib
    _options = {}
    _options.update(options)
    _options["generate_entry_cite_keys"] = False  # default is False
    _python_bib = PythonRunBib(_options)
    data_list = transform_to_data_list(zotero_bib, ".bib")
    zotero_library = _python_bib.parse_to_single_standard_library(data_list)

    # for download bib
    _options = {}
    _options.update(options)
    _options["generate_entry_cite_keys"] = True  # default is False
    _python_bib = PythonRunBib(_options)
    data_list = transform_to_data_list(download_bib, ".bib")
    download_library = _python_bib.parse_to_single_standard_library(data_list)

    # compare download bib and zotero bib
    only_in_download_entries, in_download_and_zotero_entries = [], []
    for download_entry in download_library.entries:
        flag = False
        for zotero_entry in zotero_library.entries:
            if check_equal_for_entry(zotero_entry, download_entry, ["title"], None):
                in_download_and_zotero_entries.append(download_entry)
                flag = True
                break

        if not flag:
            only_in_download_entries.append(download_entry)

    # write
    _options = {}
    _options.update(options)
    _python_write = PythonWriters(_options)
    _python_write.write_to_file(only_in_download_entries, "only_in_download.bib", "w", path_output, False)
    _python_write.write_to_file(in_download_and_zotero_entries, "in_download_and_zotero.bib", "w", path_output, False)
    return None
