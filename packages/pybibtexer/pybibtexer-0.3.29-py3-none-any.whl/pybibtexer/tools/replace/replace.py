import os
import re
from typing import Any

from pyadvtools import standard_path, transform_to_data_list, write_list

from ...bib.bibtexparser import Library
from ...main import PythonRunBib, PythonWriters


def replace_to_standard_cite_keys(
    full_tex_md: str, full_bib: str, path_output: str, options: dict[str, Any]
) -> list[str]:
    """Replace citation keys in TeX/Markdown files with standardized keys from BibTeX.

    Processes both LaTeX and Markdown files, replacing old citation keys with newly
    generated standardized keys while maintaining the corresponding BibTeX database.

    Args:
        full_tex_md: Path to TeX or Markdown file containing citations
        full_bib: Path to BibTeX file with reference entries
        path_output: Output directory for processed files
        options: Configuration options for key generation

    Returns:
        list[str]: Lines of processed text content with updated citation keys
    """
    # Validate input file type
    ext = os.path.splitext(full_tex_md)[-1]
    if ext not in [".tex", ".md", "md", "tex"]:
        print(f"{full_tex_md} must be `.tex` or `.md` file.")
        return []

    # Standardize output path and read BibTeX data
    path_output = standard_path(path_output)
    bib_data = transform_to_data_list(full_bib, ".bib")

    # Generate mapping from old to new citation keys
    old_key_new_entry_dict = generate_old_key_new_entry_dict(bib_data, options)

    # Read and process document content
    data = "".join(transform_to_data_list(full_tex_md, ext))

    # Replace citation keys in content
    for old_key, new_entry in old_key_new_entry_dict.items():
        if ext == ".tex":
            # LaTeX citation patterns: \cite{}, \citet{}, \citep{}, and so on
            data = re.sub(r"\\cite([a-z]*){\s*" + old_key + r"\s*}", r"\\cite\1{" + new_entry.key + "}", data)
            data = re.sub(r"\\cite([a-z]*){\s*" + old_key + r"\s*,", r"\\cite\1{" + new_entry.key + ",", data)
            data = re.sub(r",\s*" + old_key + r"\s*,", r"," + new_entry.key + r",", data)
            data = re.sub(r",\s*" + old_key + r"\s*}", r"," + new_entry.key + "}", data)
        elif ext == ".md":
            # Markdown citation patterns: [@], comma-separated lists
            data = re.sub(r"\[@\s*" + old_key + r"\s*\]", r"[@" + new_entry.key + "]", data)
            data = re.sub(r"\[@\s*" + old_key + r"\s*,", r"[@" + new_entry.key + ",", data)
            data = re.sub(r",\s*" + old_key + r"\s*,", r"," + new_entry.key + r",", data)
            data = re.sub(r",\s*" + old_key + r"\s*\]", r"," + new_entry.key + "]", data)
        else:
            pass

    # Write processed document
    data_list = data.splitlines(keepends=True)
    write_list(data_list, f"new{ext}", "w", path_output, False)

    # Write updated BibTeX file with new citation keys
    _options = {}
    _options.update(options)
    _options["is_sort_blocks"] = False  # Preserve original entry order and default is True
    _python_write = PythonWriters(_options)
    _python_write.write_to_file(list(old_key_new_entry_dict.values()), "new.bib", "w", path_output, False)
    return data_list


def generate_old_key_new_entry_dict(bib_data: list[str] | str, options: dict[str, Any]) -> dict:
    # Parse library without generating new keys first
    _options = {}
    _options.update(options)
    _options["generate_entry_cite_keys"] = False  # default is False
    _python_bib = PythonRunBib(_options)
    library = _python_bib.parse_to_single_standard_library(bib_data)

    # Configure for key generation
    _options = {}
    _options.update(options)
    _options["generate_entry_cite_keys"] = True  # default is False
    _python_bib = PythonRunBib(_options)

    # Generate new keys for each entry
    old_key_new_entry_dict = {}
    generate_cite_keys: list[str] = []  # Track generated keys to ensure uniqueness

    for old_key in (entries_dict := library.entries_dict):
        new_library = _python_bib.parse_to_single_standard_library(Library([entries_dict[old_key]]))

        if len(new_library.entries) == 1:
            new_entry = new_library.entries[0]

            # Ensure key uniqueness by appending suffix if needed
            new_key = new_entry.key
            while new_key in generate_cite_keys:
                new_key += "-a"
            new_entry.key = new_key

            # save
            generate_cite_keys.append(new_entry.key)
            old_key_new_entry_dict[old_key] = new_entry

        else:
            # Keep original entry if processing fails
            old_key_new_entry_dict[old_key] = entries_dict[old_key]

    return old_key_new_entry_dict
