import copy
import math
import os
import re
from typing import Any

from pyadvtools import (
    IterateCombineExtendDict,
    read_list,
    sort_int_str,
    standard_path,
    transform_to_data_list,
    write_list,
)

from ..bib.bibtexparser import Block, Library
from ..main import PythonRunBib, PythonWriters
from ..tools.experiments_base import generate_readme


def format_bib_to_save_mode_by_entry_type(
    c_j_abbr: str,
    path_output: str,
    original_data: list[str] | str | Library,
    combine_year_length: int = 1,
    default_year_list: list[str] | None = None,
    write_flag_bib: str = "w",
    check_bib_exist: bool = False,
    write_flag_readme: str = "w",
    check_md_exist: bool = False,
    options: dict[str, Any] | None = None,
) -> None:
    """Formats bibliography entries and organizes them by year and type.

    Processes bibliography data and organizes it into separate files by entry type and year,
    generating both BibTeX files and README documentation.

    Args:
        c_j_abbr: Conference/Journal abbreviation used for naming output files.
        path_output: Output directory path for processed files.
        original_data: Input bibliography data in various formats (list of strings,
            file path, file, raw string, or Library object).
        combine_year_length: Number of years to combine in each output file.
        default_year_list: Specific years to process (if empty, processes all years).
        write_flag_bib: Write mode for BibTeX files ("w" for write, "a" for append).
        check_bib_exist: Whether to check if BibTeX files exist before writing.
        write_flag_readme: Write mode for README files ("w" for write, "a" for append).
        check_md_exist: Whether to check if README files exist before writing.
        options: Additional processing options.

    Returns:
        None
    """
    if default_year_list is None:
        default_year_list = []

    if options is None:
        options = {}

    path_output = standard_path(path_output)

    # Set up processing options.
    _options = {}
    _options.update(options)
    _options["is_sort_entry_fields"] = True  # Force field sorting.
    _options["is_sort_blocks"] = True  # Force block sorting.
    _options["sort_entries_by_field_keys_reverse"] = False  # Sort in ascending order, default is True.

    # Initialize helper classes.
    _python_bib = PythonRunBib(_options)

    _options["empty_entry_cite_keys"] = True  # Allow empty citation keys.
    _python_writer = PythonWriters(_options)

    # Organize entries by type, year, volume, number, and month.
    entry_type_year_volume_number_month_entry_dict = _python_bib.parse_to_nested_entries_dict(original_data)

    # Process each entry type separately.
    for entry_type in entry_type_year_volume_number_month_entry_dict:
        # Filter years if specified.
        year_dict = entry_type_year_volume_number_month_entry_dict[entry_type]
        year_list = sort_int_str(list(year_dict.keys()))
        if default_year_list:
            year_list = [y for y in year_list if y in default_year_list]
        year_dict = {year: year_dict[year] for year in year_list}

        # Save bibliography files grouped by years.
        path_write = os.path.join(path_output, entry_type.lower(), "bib")
        for i in range(math.ceil(len(year_list) / combine_year_length)):
            # Determine year range for this file.
            start_year_index = i * combine_year_length
            end_year_index = min([(i + 1) * combine_year_length, len(year_list)])
            combine_year = year_list[start_year_index:end_year_index]

            # Create subset dictionary for these years.
            new_year_dict = {year: year_dict[year] for year in combine_year}
            entries: list[Block] = IterateCombineExtendDict().dict_update(copy.deepcopy(new_year_dict))

            # Generate filename based on year range.
            name = f"{c_j_abbr}_{combine_year[0]}"
            if len(combine_year) > 1:
                name += f"_{combine_year[-1]}"
            name += ".bib"

            # Write the bibliography file.
            _python_writer.write_to_file(entries, name, write_flag_bib, path_write, check_bib_exist)

        # Generate and save README documentation.
        path_write = os.path.join(path_output, entry_type.lower())
        readme_md = generate_readme(c_j_abbr, entry_type, year_dict)

        # Handle append mode for README.
        if re.search("a", write_flag_readme):
            old_readme_md = [re.sub(r"[ ]+", "", line) for line in read_list("README.md", "r", path_write)]
            readme_md = readme_md[3:] if old_readme_md else readme_md
            readme_md = [line for line in readme_md if re.sub(r"[ ]+", "", line) not in old_readme_md]

        write_list(readme_md, "README.md", write_flag_readme, path_write, check_md_exist)


def generate_statistic_information(path_storage: str) -> None:
    """Generates statistical information from bibliography files.

    Processes all BibTeX files in the directory tree and extracts key information
    (DOIs and URLs) into CSV files for analysis.

    Args:
        path_storage: Root directory containing BibTeX files to process.

    Returns:
        None
    """
    # Find all BibTeX files in the directory tree.
    full_files = []
    for root, _, files in os.walk(path_storage):
        full_files.extend([os.path.join(root, f) for f in files if f.endswith(".bib")])

    # Configure processing options.
    _options = {
        "is_standardize_bib": False,  # Skip standardization, default is True.
        "choose_abbr_zotero_save": "save",  # Use save format, default is "save".
        "delete_field_list_for_save": [],  # Do not delete any fields, default is [].
        "function_common_again": False,  # Skip reprocessing, default is True.
        "function_common_again_abbr": False,  # Skip abbreviation reprocessing, default is True.
        "function_common_again_zotero": False,  # Skip Zotero reprocessing, default is True.
        "function_common_again_save": False,  # Skip save format reprocessing, default is True.
        "is_sort_entry_fields": False,  # Skip field sorting.
        "is_sort_blocks": False,  # Skip block sorting.
    }
    _python_bib = PythonRunBib(_options)

    # Process each BibTeX file.
    for f in full_files:
        informations = []
        library = _python_bib.parse_to_single_standard_library(f)

        # Extract DOI or URL for each entry.
        for entry in library.entries:
            flag = ""
            if not flag:
                flag = entry["doi"] if "doi" in entry else ""
            if not flag:
                flag = entry["url"] if "url" in entry else ""
            informations.append(flag + "\n")

        # Write information to CSV file.
        csv_path = f.replace(".bib", ".csv").replace(f"{os.sep}bib{os.sep}", f"{os.sep}url{os.sep}")
        write_list(informations, csv_path, "w", None, False)

    return None


def format_bib_to_abbr_zotero_save_modes(
    original_data: list[str] | str, path_output: str, options: dict[str, Any]
) -> None:
    """Formats bibliography data to multiple standard formats.

    Processes bibliography data and generates three standardized formats:
    abbreviated format, Zotero format, and save format.

    Args:
        original_data: Input bibliography data as list of strings or file path.
        path_output: Output directory path for processed files.
        options: Processing configuration options.

    Returns:
        None
    """
    path_output = standard_path(path_output)

    # Generate for original data.
    data_list = transform_to_data_list(original_data, ".bib")

    # Parse data to abbr_library, zotero_library, and save_library.
    _options = {}
    _options.update(options)
    _python_bib = PythonRunBib(_options)
    abbr_library, zotero_library, save_library = _python_bib.parse_to_multi_standard_library(data_list)

    # Write with sorting blocks according to original cite keys.
    _options = {}
    _options.update(options)
    _options["is_sort_entry_fields"] = options.get("is_sort_entry_fields", True)  # Default is True.
    _options["is_sort_blocks"] = options.get("is_sort_blocks", False)  # Default is True.
    _python_write = PythonWriters(_options)
    _python_write.write_multi_library_to_multi_file(path_output, abbr_library, zotero_library, save_library)


def format_bib_to_abbr_or_zotero_or_save_mode(
    original_data: list[str] | str, options: dict[str, Any]
) -> tuple[list[str], list[str], list[str]]:
    """Formats bibliography data to multiple standard formats and returns as data lists.

    Processes bibliography data and generates three standardized formats as string lists:
    abbreviated format, Zotero format, and save format.

    Args:
        original_data: Input bibliography data as list of strings or file path.
        options: Processing configuration options.

    Returns:
        Tuple containing three lists of strings representing the formatted bibliography data
        in abbreviated, Zotero, and save formats.
    """
    # Generate for original data.
    data_list = transform_to_data_list(original_data, ".bib")

    # Parse data to abbr_library, zotero_library, and save_library.
    _options = {}
    _options.update(options)
    _python_bib = PythonRunBib(_options)
    abbr_library, zotero_library, save_library = _python_bib.parse_to_multi_standard_library(data_list)

    # Write with sorting blocks according to original cite keys.
    _options = {}
    _options.update(options)
    _options["is_sort_entry_fields"] = options.get("is_sort_entry_fields", True)  # Default is True.
    _options["is_sort_blocks"] = options.get("is_sort_blocks", False)  # Default is True.
    _python_write = PythonWriters(_options)
    return _python_write.write_multi_library_to_multi_data_list(abbr_library, zotero_library, save_library)
