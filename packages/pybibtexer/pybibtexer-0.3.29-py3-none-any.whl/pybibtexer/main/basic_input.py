import os
import re
from typing import Any

from .utils import (
    CheckAcronymAbbrAndFullDict,
    StrictOrderedDict,
    load_json_file,
    process_user_conferences_journals_json,
)


class BasicInput:
    """Basic input.

    Args:
        options (dict[str, Any]): Options.

    Attributes:
        full_abbr_article_dict (dict[str, str]): Full abbr article dict.
        full_abbr_inproceedings_dict (dict[str, str]): Full abbr inproceedings dict.
        full_names_in_json (str): Full names in json.
        abbr_names_in_json (str): Abbr names in json.
        abbr_article_pattern_dict (dict): Pre-compiled regex patterns for journal name matching
        abbr_inproceedings_pattern_dict (dict): Pre-compiled regex patterns for conference name matching

        options (dict[str, Any]): Options.

    Notes:
        full_json_c (str): User-provided JSON file containing conference data.
        full_json_j (str): User-provided JSON file containing journal data.

    """

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize the processor with configuration options.

        Args:
            options: Configuration dictionary containing processing parameters
        """
        # Load special abbreviations for conferences and journals from built-in templates
        special_abbr_dict_c = self._process_build_in_json("conferences_special.json")
        special_abbr_dict_j = self._process_build_in_json("journals_special.json")

        # Load default abbreviations for conferences and journals from built-in templates
        default_abbr_dict_c = self._process_build_in_json("conferences.json")
        default_abbr_dict_j = self._process_build_in_json("journals.json")

        # Load user-defined abbreviations from provided JSON files
        full_json_c, full_json_j = options.get("full_json_c", ""), options.get("full_json_j", "")
        user_abbr_dict_c, user_abbr_dict_j = process_user_conferences_journals_json(full_json_c, full_json_j)

        # Merge dictionaries with precedence: user > default
        # Articles use journal abbreviations, inproceedings use conference abbreviations
        full_abbr_article_dict = {**default_abbr_dict_j, **user_abbr_dict_j}
        full_abbr_inproceedings_dict = {**default_abbr_dict_c, **user_abbr_dict_c}

        # TODO: Whether to check?
        # Check for duplicate acronyms and abbreviations in the dictionaries
        # check = CheckAcronymAbbrAndFullDict()
        # full_abbr_article_dict = check.length_dupicate_match(full_abbr_article_dict)[0]
        # full_abbr_inproceedings_dict = check.length_dupicate_match(full_abbr_inproceedings_dict)[0]

        # Merge dictionaries with precedence: merged (user + default) > special
        # Articles use journal abbreviations, inproceedings use conference abbreviations
        full_abbr_article_dict = {**special_abbr_dict_j, **full_abbr_article_dict}
        full_abbr_inproceedings_dict = {**special_abbr_dict_c, **full_abbr_inproceedings_dict}

        # Convert to strict ordered dictionaries to maintain consistent ordering
        full_abbr_article_dict = StrictOrderedDict(full_abbr_article_dict)
        full_abbr_inproceedings_dict = StrictOrderedDict(full_abbr_inproceedings_dict)

        # Define JSON field names for full and abbreviated names
        full_names_in_json = "names_full"
        abbr_names_in_json = "names_abbr"

        # Pre-compile regex patterns for efficient text matching
        abbr_article_pattern_dict, abbr_inproceedings_pattern_dict = self.abbr_article_inproceedings_pattern(
            full_abbr_article_dict, full_abbr_inproceedings_dict, full_names_in_json, abbr_names_in_json
        )

        # Convert pattern dictionaries to strict ordered dictionaries
        abbr_article_pattern_dict = StrictOrderedDict(abbr_article_pattern_dict)
        abbr_inproceedings_pattern_dict = StrictOrderedDict(abbr_inproceedings_pattern_dict)

        # Store all configurations in options for later use by other methods
        options["full_abbr_article_dict"] = full_abbr_article_dict
        options["full_abbr_inproceedings_dict"] = full_abbr_inproceedings_dict
        options["full_names_in_json"] = full_names_in_json
        options["abbr_names_in_json"] = abbr_names_in_json
        options["abbr_article_pattern_dict"] = abbr_article_pattern_dict
        options["abbr_inproceedings_pattern_dict"] = abbr_inproceedings_pattern_dict

        self.options = options

    @staticmethod
    def abbr_article_inproceedings_pattern(
        full_abbr_article_dict: StrictOrderedDict,
        full_abbr_inproceedings_dict: StrictOrderedDict,
        full_names_in_json: str,
        abbr_names_in_json: str,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
        """Pre-compile regex patterns for journal and conference name matching.

        Args:
            full_abbr_article_dict: dictionary containing journal abbreviations and their full names
            full_abbr_inproceedings_dict: dictionary containing conference abbreviations and their full names
            full_names_in_json: Key for full names in the dictionary
            abbr_names_in_json: Key for abbreviation names in the dictionary

        Returns:
            Tuple of two dictionaries containing pre-compiled regex patterns for journals and conferences
        """

        def _create_pattern_dict(abbr_dict: StrictOrderedDict) -> dict[str, dict[str, Any]]:
            """Helper function to create pattern dictionary for a given abbreviation dictionary."""
            pattern_dict = {}
            for abbr, abbr_info in abbr_dict.items():
                # Get all name variations and combine with abbreviation
                full_names = abbr_info.get(full_names_in_json, [])
                long_abbrs = abbr_info.get(abbr_names_in_json, [])
                all_names = [*full_names, *long_abbrs, abbr]
                all_names = [m.lower() for m in all_names]

                # Create pre-compiled regex pattern for exact matching
                pattern_dict[abbr] = {
                    "pattern": re.compile(rf"^({'|'.join(all_names)})$", flags=re.I),
                    "names": all_names,
                }
            return pattern_dict

        abbr_article_pattern_dict = _create_pattern_dict(full_abbr_article_dict)
        abbr_inproceedings_pattern_dict = _create_pattern_dict(full_abbr_inproceedings_dict)

        return abbr_article_pattern_dict, abbr_inproceedings_pattern_dict

    def _process_build_in_json(self, json_name: str) -> dict:
        """Process conferences or journals JSON file from built-in templates.

        Notes:
            The structure of JSON follows the format:
                {"abbr": {"names_abbr": [], "names_full": []}}

        Returns:
            Dictionary containing the processed JSON data
        """
        # Get current directory and construct path to templates
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_templates = os.path.join(os.path.dirname(current_dir), "data", "templates")

        # Load and return JSON dictionary
        full_json = os.path.join(path_templates, "abbr_full", json_name)
        full_abbr_dict = load_json_file(full_json)

        return full_abbr_dict
