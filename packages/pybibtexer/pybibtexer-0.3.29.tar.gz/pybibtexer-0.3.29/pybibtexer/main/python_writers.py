import os
import re
from typing import Any

from pyadvtools import write_list

from ..bib.bibtexparser import BibtexFormat, Block, Entry, Library
from ..bib.core import ConvertLibrayToStr
from .basic_input import BasicInput


class PythonWriters(BasicInput):
    r"""Python writers for generating BibTeX files with various formatting options.

    Args:
        options (dict[str, Any]): Configuration options for BibTeX generation.
            - is_sort_entry_fields (bool): Whether to sort entry fields (default: True)
            - is_sort_blocks (bool): Whether to sort bibliography blocks (default: True)
            - sort_entries_by_field_keys_reverse (bool): Reverse sort order for entries (default: True)
            - choose_abbr_zotero_save (str): Source selection - "abbr", "zotero", or "save" (default: "save")

    Attributes:
        choose_abbr_zotero_save (str): Selected bibliography purpose ("abbr", "zotero", or "save")
        bib_name_for_abbr (str): Filename for abbreviated bibliography (default: "abbr.bib")
        bib_name_for_zotero (str): Filename for Zotero bibliography (default: "zotero.bib")
        bib_name_for_save (str): Filename for saved bibliography (default: "save.bib")
        join_flag_in_http (str): The join flag for HTTP-related formatting (default: " | " or " |\n")
        display_www_google_connected_scite (list[str]): Display options selection from
            ["www", "google", "connected", "scite"]
        bibtex_format_indent (str): Indentation string for BibTeX formatting (default: "  ")
        bibtex_format_trailing_comma (bool): Whether to include trailing commas in BibTeX entries (default: True)
        bibtex_format_block_separator (str): Separator between BibTeX blocks (default: "")
    """

    def __init__(self, options: dict[str, Any]) -> None:
        # Set default options if not provided
        options["choose_abbr_zotero_save"] = options.get("choose_abbr_zotero_save", "save")
        options["is_sort_entry_fields"] = options.get("is_sort_entry_fields", True)
        options["is_sort_blocks"] = options.get("is_sort_blocks", True)
        options["sort_entries_by_field_keys_reverse"] = options.get("sort_entries_by_field_keys_reverse", True)
        super().__init__(options)

        # Initialize bibliography source filenames
        self.bib_name_for_abbr = options.get("bib_name_for_abbr", "abbr.bib")
        self.bib_name_for_zotero = options.get("bib_name_for_zotero", "zotero.bib")
        self.bib_name_for_save = options.get("bib_name_for_save", "save.bib")

        self.join_flag_in_http = options.get("join_flag_in_http", " | ")  # " |\n"

        # Initialize display options
        self.display_www_google_connected_scite = options.get(
            "display_www_google_connected_scite", ["www", "google", "connected", "scite"]
        )

        # Initialize BibTeX formatting options
        self.bibtex_format_indent = options.get("bibtex_format_indent", "  ")
        self.bibtex_format_trailing_comma = options.get("bibtex_format_trailing_comma", True)
        self.bibtex_format_block_separator = options.get("bibtex_format_block_separator", "")

        # Create and configure BibtexFormat object
        bibtex_format = BibtexFormat()
        bibtex_format.indent = self.bibtex_format_indent
        bibtex_format.block_separator = self.bibtex_format_block_separator
        bibtex_format.trailing_comma = self.bibtex_format_trailing_comma
        self._bibtex_format: BibtexFormat = bibtex_format

    def write_to_str(self, library: Library | list[Block]) -> list[str]:
        """Serialize a BibTeX database to a string.

        Args:
            library (Library | list[Block]): BibTeX database to serialize.

        """
        return ConvertLibrayToStr(self.options).generate_str(library, self._bibtex_format)

    def write_to_file(
        self,
        original_data: Library | list[Block] | list[str],
        file_name: str,
        write_flag: str = "w",
        path_storage: str | None = None,
        check: bool = True,
        delete_first_empty: bool = True,
        delete_last_empty: bool = True,
        compulsory: bool = False,
        delete_original_file: bool = False,
    ) -> None:
        """Write.

        Args:
            original_data (Union[Library, list[Block], list[str]]): data
            file_name (str): file name
            write_flag (str = "w"): write flag
            path_storage (Optional[str] = None): path storage
            check (bool = True): check
            delete_first_empty (bool = True): delete first empty
            delete_last_empty (bool = True): delete last empty
            compulsory (bool = False): compulsory
            delete_original_file (bool = False): delete original file

        """
        _options = {}
        _options.update(self.options)
        _library_str = ConvertLibrayToStr(_options)

        if isinstance(original_data, Library):
            data_list = _library_str.generate_str(original_data, self._bibtex_format)
        elif isinstance(original_data, list):
            if all(isinstance(line, str) for line in original_data):
                data_list = [line for line in original_data if isinstance(line, str)]
            else:
                data_list = [line for line in original_data if isinstance(line, Block)]
                data_list = _library_str.generate_str(data_list, self._bibtex_format)

        write_list(
            data_list,
            file_name,
            write_flag,
            path_storage,
            check,
            delete_first_empty,
            delete_last_empty,
            compulsory,
            delete_original_file,
        )
        return None

    def write_multi_library_to_multi_file(
        self,
        path_output: str,
        bib_for_abbr: Library | list[Block],
        bib_for_zotero: Library | list[Block],
        bib_for_save: Library | list[Block],
        given_cite_keys: list[str] | None = None,
        **kwargs,
    ) -> tuple[str, str, str]:
        if given_cite_keys is None:
            given_cite_keys = []

        _options = {}
        _options.update(self.options)
        _options["keep_entries_by_cite_keys"] = given_cite_keys
        _options["sort_entries_by_cite_keys"] = given_cite_keys

        bib_abbr = ConvertLibrayToStr(_options).generate_str(bib_for_abbr, **kwargs)
        write_list(bib_abbr, self.bib_name_for_abbr, "w", path_output, False, **kwargs)

        bib_zotero = ConvertLibrayToStr(_options).generate_str(bib_for_zotero, **kwargs)
        write_list(bib_zotero, self.bib_name_for_zotero, "w", path_output, False, **kwargs)

        bib_save = ConvertLibrayToStr(_options).generate_str(bib_for_save, **kwargs)
        write_list(bib_save, self.bib_name_for_save, "w", path_output, False, **kwargs)

        full_bib_for_abbr = os.path.join(path_output, self.bib_name_for_abbr)
        full_bib_for_zotero = os.path.join(path_output, self.bib_name_for_zotero)
        full_bib_for_save = os.path.join(path_output, self.bib_name_for_save)
        return full_bib_for_abbr, full_bib_for_zotero, full_bib_for_save

    def write_multi_library_to_multi_data_list(
        self,
        bib_for_abbr: Library | list[Block],
        bib_for_zotero: Library | list[Block],
        bib_for_save: Library | list[Block],
        given_cite_keys: list[str] | None = None,
        **kwargs,
    ) -> tuple[list[str], list[str], list[str]]:
        if given_cite_keys is None:
            given_cite_keys = []

        _options = {}
        _options.update(self.options)
        _options["keep_entries_by_cite_keys"] = given_cite_keys
        _options["sort_entries_by_cite_keys"] = given_cite_keys

        bib_abbr = ConvertLibrayToStr(_options).generate_str(bib_for_abbr, **kwargs)

        bib_zotero = ConvertLibrayToStr(_options).generate_str(bib_for_zotero, **kwargs)

        bib_save = ConvertLibrayToStr(_options).generate_str(bib_for_save, **kwargs)
        return bib_abbr, bib_zotero, bib_save

    def output_key_url_http_bib_dict(self, library: Library) -> dict[str, list[list[str]]]:
        _options = {}
        _options.update(self.options)
        _options["empty_entry_cite_keys"] = True

        key_url_http_bib_dict: dict[str, list[list[str]]] = {}

        for key, entry in library.entries_dict.items():
            url, link_list = self._generate_link_list(entry)
            patch_bib = ConvertLibrayToStr(_options).generate_str([entry])

            v: list[list[str]] = [[], [], patch_bib]

            if len(url) != 0:
                v[0] = [url + "\n"]

            join_link = []
            if link_list:
                for i in range(len(link_list) - 1):
                    join_link.append(link_list[i].strip() + self.join_flag_in_http)  # " |\n"
                join_link.append(link_list[-1].strip() + "\n")

                join_link[0] = "(" + join_link[0]
                join_link[-1] = join_link[-1].strip() + ")\n"

                v[1] = join_link

            key_url_http_bib_dict.update({key: v})
        return key_url_http_bib_dict

    def _generate_link_list(self, entry: Entry) -> tuple[str, list[str]]:
        title = entry["title"] if "title" in entry else ""
        if not title:
            return "", []

        url = entry["url"] if "url" in entry else ""
        if len(url) == 0:
            url = entry["doi"] if "doi" in entry else ""
            if (len(url) != 0) and (not re.match(r"https*://", url)):
                url = f"https://doi.org/{url}"
        www = f"[www]({url})" if url else ""

        title = re.sub(r"\s+", "+", title)
        url_google = f"https://scholar.google.com/scholar?q={title}"
        url_connected = f"https://www.connectedpapers.com/search?q={title}"
        url_scite = f"https://scite.ai/search?q={title}"

        # Search cited number
        cited_number = entry["annotation"] if "annotation" in entry else ""
        if cited_number:
            cited_number = re.sub(r"[^0-9]+", "", cited_number)
            cited_number = int(cited_number) if cited_number.isdigit() else ""
            google = f"[Google Scholar: {cited_number}]({url_google})"
        else:
            google = f"[Google Scholar]({url_google})"

        connected = f"[Connected Papers]({url_connected})"
        scite = f"[Scite]({url_scite})"

        link_list = []
        for i, j in zip(["www", "google", "connected", "scite"], [www, google, connected, scite], strict=True):
            if i in self.display_www_google_connected_scite:
                if j:
                    link_list.append(j)

        return url, link_list
