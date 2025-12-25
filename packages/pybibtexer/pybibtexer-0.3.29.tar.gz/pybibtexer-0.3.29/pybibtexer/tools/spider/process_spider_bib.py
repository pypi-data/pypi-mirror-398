import copy
import os
import re
import time

from pyadvtools import IterateCombineExtendDict, iterate_obtain_full_file_names, read_list, standard_path, write_list

from ...bib.bibtexparser.library import Library
from ...main import PythonRunBib, PythonWriters
from ..experiments_base import generate_readme
from ..format_save_bibs import format_bib_to_save_mode_by_entry_type, generate_statistic_information

EXCLUDE_ABBR_LIST = ["arxiv", "biorxiv", "ssrn"]


class ProcessSpiderBib:
    """Process spider bib.

    Args:
        path_abbr: The path of the abbreviation folder.
        abbr_standard: The standard abbreviation.

    Attributes:
        path_abbr: The path of the abbreviation folder.
        abbr_standard: The standard abbreviation.
    """

    def __init__(self, path_abbr: str, abbr_standard: str) -> None:
        self.path_abbr = os.path.expandvars(os.path.expanduser(path_abbr))
        self.abbr_standard = abbr_standard

        self._options = {
            "is_standardize_bib": True,  # default is True
            "substitute_old_list": [
                r"(<[a-zA-Z\-]+\s*/*\s*>)",
                r"(</[a-zA-Z\-]+>)",
                r'(<[a-zA-Z\-]+ [^\s]+="[^>]+?"\s*/*\s*>)',
                r"([ ]+)",
                r";[; ]*;",
                r",[, ]*,",
            ],
            "substitute_new_list": ["", "", "", " ", ";", ","],
            "choose_abbr_zotero_save": "save",  # default is "save"
            "delete_field_list_for_save": [],  # default is []
            "is_sort_entry_fields": True,  # default is False
            "is_sort_blocks": True,  # default is False
            "sort_entries_by_field_keys_reverse": False,  # default is True
            "empty_entry_cite_keys": True,
        }

        self._python_bib = PythonRunBib(self._options)

    def format_spider_bib(self, write_bib: bool = False) -> None:
        """Format spider bib."""
        file_list = iterate_obtain_full_file_names(self.path_abbr, ".bib", False)

        if write_bib:
            if os.path.exists(readme := os.path.join(self.path_abbr, "README.md")):
                os.remove(readme)

        _options = {}
        _options.update(self._options)
        _python_writer = PythonWriters(_options)

        for f in file_list:
            print("*" * 5 + f" Format {os.path.basename(f)} " + "*" * 5)

            data_list = read_list(f, "r")

            # standardize
            entry_type_year_volume_number_month_entry_dict = self._python_bib.parse_to_nested_entries_dict(data_list)
            if not write_bib:
                continue

            # just for the necessary part
            old_readme_md = [re.sub(r"[ ]+", "", line) for line in read_list("README.md", "r", self.path_abbr)]
            new_readme_md = []
            new_entry_list = []

            for entry_type in entry_type_year_volume_number_month_entry_dict:
                new_dict = entry_type_year_volume_number_month_entry_dict.get(entry_type.lower(), {})

                # for README.md
                readme_md = generate_readme(self.abbr_standard, entry_type.lower(), new_dict)
                readme_md = readme_md[3:] if (old_readme_md or new_readme_md) else readme_md
                readme_md = [line for line in readme_md if re.sub(r"[ ]+", "", line) not in old_readme_md]
                new_readme_md.extend(readme_md)

                # for bib
                entry_list = IterateCombineExtendDict().dict_update(copy.deepcopy(new_dict))
                new_entry_list.extend(entry_list)

            write_list(new_readme_md, "README.md", "a", self.path_abbr, False)
            _python_writer.write_to_file(new_entry_list, f, "w", None, False)
        return None

    def check_spider_bib(self, delete_duplicate_in_bibs: bool = False) -> None:
        """Check bib."""
        bibs_name = iterate_obtain_full_file_names(self.path_abbr, ".bib", False)
        bibs_name = [[f, os.path.basename(f).split(".")[0].strip()] for f in bibs_name]

        urls_name = iterate_obtain_full_file_names(self.path_abbr, ".csv", False)
        urls_name = [[f, os.path.basename(f).split(".")[0].strip()] for f in urls_name]

        url_base_names = [name[-1] for name in urls_name]

        _options = {}
        _options.update(self._options)
        _python_writer = PythonWriters(_options)

        for name in bibs_name:
            bib_base_name = name[-1]
            if bib_base_name not in url_base_names:
                print(f"{bib_base_name}.csv not in the folder `url`.")
                continue

            full_bib, full_url = name[0], urls_name[url_base_names.index(bib_base_name)][0]

            print("*" * 5 + f" Check {os.path.basename(full_bib)} and {os.path.basename(full_url)} " + "*" * 5)
            bib_list = read_list(full_bib, "r")

            # Check duplicated blocks in bib file
            library = self._python_bib.parse_to_single_standard_library(bib_list)

            url_bib_dict = {}
            for entry in library.entries:
                doi = entry["doi"] if "doi" in entry else ""
                url_ = entry["url"] if "url" in entry else ""
                url = doi if doi else url_
                url_bib_dict.setdefault(url, []).append(entry)

            duplicate_url, new_entries = [], []
            for url in url_bib_dict:
                if len(url_bib_dict[url]) > 1:
                    duplicate_url.append(url)
                if delete_duplicate_in_bibs:
                    new_entries.append(url_bib_dict[url][0])

            # Delete duplicated blocks in bib file
            if duplicate_url:
                print(f"Duplicates in {full_bib}: {duplicate_url}\n")
            if duplicate_url and delete_duplicate_in_bibs:
                _python_writer.write_to_file(new_entries, full_bib, "w", None, False)
        return None

    def move_spider_bib(self, path_shutil: str) -> None:
        if self.abbr_standard.lower() in EXCLUDE_ABBR_LIST:
            return None

        # Move
        print("*" * 5 + f" Start moving {self.abbr_standard} ... " + "*" * 5)
        path_move = os.path.join(path_shutil, self.abbr_standard)
        entry_type_entry_dict = {}
        library = PythonRunBib({}).parse_to_single_standard_library(self.path_abbr)
        for entry in library.entries:
            entry_type_entry_dict.setdefault(entry.entry_type, []).append(entry)
        for entry_type in entry_type_entry_dict:
            format_bib_to_save_mode_by_entry_type(
                self.abbr_standard,
                path_move,
                Library(entry_type_entry_dict[entry_type]),
                combine_year_length=1,
                default_year_list=self._default_year_list(entry_type),
                write_flag_bib="a",
                check_bib_exist=False,
                write_flag_readme="a",
                check_md_exist=False,
                options=self._options,
            )
        generate_statistic_information(path_move)
        print("*" * 5 + " Successfully moving ... " + "*" * 5)

        # Delete
        _options = {}
        _options.update(self._options)
        _python_writer = PythonWriters(_options)
        print("*" * 5 + f" Start deleting {self.abbr_standard} ... " + "*" * 5)
        bibs = iterate_obtain_full_file_names(self.path_abbr, ".bib")
        for bib in bibs:
            new_entries = []
            library = self._python_bib.parse_to_single_standard_library(read_list(bib, "r"))
            for entry in library.entries:
                year = entry["year"] if "year" in entry else ""
                if year not in self._default_year_list(entry.entry_type):
                    new_entries.append(entry)
            _python_writer.write_to_file(new_entries, bib, "w", None, False, True, True, False, True)
        print("*" * 5 + " Successfully deleting ... " + "*" * 5)

    @staticmethod
    def _default_year_list(entry_type) -> list:
        year = int(time.strftime("%Y", time.localtime()))
        month = int(time.strftime("%m", time.localtime()))
        m = 0 if month <= 3 else 1
        if entry_type == "article":
            default_year_list = [str(i) for i in range(1800, year + m - 1)]
        elif entry_type == "inproceedings":
            default_year_list = [str(i) for i in range(1800, year + 2)]
        else:
            default_year_list = [str(i) for i in range(1800, year + m - 1)]
        return default_year_list

    def simplify_early_access(self):
        # for IEEE Early Access
        path_ieee_early_access = self.path_abbr
        path_ieee = path_ieee_early_access.replace("spider_j_e", "spider_j")

        _options = {}
        _options.update(self._options)
        _python_writer = PythonWriters(_options)

        print(f"***** Simplify {self.abbr_standard} *****")
        path_url_ieee_early_access = os.path.join(path_ieee_early_access, "url")
        path_bib_ieee_early_access = os.path.join(path_ieee_early_access, "bib")
        path_url_ieee = os.path.join(path_ieee, "url")

        # for txt urls
        data_list = read_list(f"{self.abbr_standard}_0.txt", "r", path_url_ieee_early_access)
        for name in [f for f in os.listdir(path_url_ieee) if f.endswith(".txt")]:
            temp_data_list = read_list(name, "r", path_url_ieee)
            data_list = list(set(data_list).difference(set(temp_data_list)))
        write_list(sorted(data_list), f"{self.abbr_standard}_0.txt", "w", path_url_ieee_early_access, False)

        # for csv urls
        data_list_csv = read_list(f"{self.abbr_standard}_0.csv", "r", path_url_ieee_early_access)
        data_list_txt = read_list(f"{self.abbr_standard}_0.txt", "r", path_url_ieee_early_access)
        data_list = list(set(data_list_csv).intersection(set(data_list_txt)))
        write_list(sorted(data_list), f"{self.abbr_standard}_0.csv", "w", path_url_ieee_early_access, False)

        # for bibs
        data_list_bib = read_list(f"{self.abbr_standard}_0.bib", "r", path_bib_ieee_early_access)
        data_list_url = read_list(f"{self.abbr_standard}_0.txt", "r", path_url_ieee_early_access)

        entries = []
        library = self._python_bib.parse_to_single_standard_library(data_list_bib)
        for url in data_list_url:
            for entry in library.entries:
                if standard_path(url) == standard_path(entry["url"]):
                    entries.append(entry)
                    break

        _python_writer.write_to_file(
            entries, f"{self.abbr_standard}_0.bib", "w", path_bib_ieee_early_access, False, True, True, True
        )
