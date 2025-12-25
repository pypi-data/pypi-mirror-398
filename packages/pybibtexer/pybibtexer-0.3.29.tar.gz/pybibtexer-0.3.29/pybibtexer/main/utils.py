import re
from typing import Any

from ..utils.utils import load_json_file


class StrictOrderedDict:
    """A dictionary that strictly maintains insertion order.

    This implementation guarantees that keys, values, and items will always be
    returned in the exact order they were inserted, regardless of Python version
    or internal dictionary implementation changes.

    Attributes:
        _keys: List maintaining the order of key insertion.
        _data: Dictionary storing the actual key-value pairs.
    """

    def __init__(self, data: dict) -> None:
        """Initializes the StrictOrderedDict with optional initial data.

        Args:
            data: Optional iterable of (key, value) pairs to initialize the dictionary.
                  If provided, must be an iterable containing exactly two-element
                  tuples or lists representing key-value pairs.

        Example:
            >>> sod = StrictOrderedDict()
            >>> sod = StrictOrderedDict([('a', 1), ('b', 2)])
        """
        self._keys = []  # Maintains insertion order of keys
        self._data = {}  # Stores the actual key-value mappings

        if data:
            for k, v in data.items():
                self[k] = v

    def __setitem__(self, key: str, value: Any) -> None:
        """Sets a key-value pair, maintaining insertion order for new keys.

        Args:
            key: The key to set or update.
            value: The value to associate with the key.

        Note:
            If the key is new, it is added to the end of the insertion order.
            If the key exists, its value is updated but its position remains unchanged.
        """
        if key not in self._data:
            self._keys.append(key)  # Only add new keys to maintain order

        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        """Retrieves the value associated with the given key.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key.

        Raises:
            KeyError: If the key is not found in the dictionary.
        """
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Support key in dict syntax.

        Args:
            key: The key to check for existence.

        Returns:
            True if key exists in the dictionary, False otherwise.
        """
        return key in self._data

    def __len__(self) -> int:
        """Support len(dict) syntax.

        Returns:
            The number of items in the dictionary.
        """
        return len(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        """Safely get a value by key, returning default if key doesn't exist.

        Args:
            key: The key to look up.
            default: Value to return if key is not found. Defaults to None.

        Returns:
            The value associated with the key, or default if key doesn't exist.
        """
        return self._data.get(key, default)

    def keys(self) -> list[str]:
        """Returns all keys in insertion order.

        Returns:
            A copy of the list containing all keys in the order they were inserted.
        """
        return self._keys.copy()

    def values(self) -> list[Any]:
        """Returns all values in key insertion order.

        Returns:
            A list of values in the same order as their corresponding keys were inserted.
        """
        return [self._data[k] for k in self._keys]

    def items(self) -> list[tuple[str, Any]]:
        """Returns all key-value pairs in insertion order.

        Returns:
            A list of (key, value) tuples in the order they were inserted.
        """
        return [(k, self._data[k]) for k in self._keys]

    def __repr__(self) -> str:
        """Returns a string representation of the dictionary.

        Returns:
            A string representation showing all key-value pairs in insertion order,
            formatted like a standard Python dictionary.

        Example:
            >>> sod = StrictOrderedDict([('x', 10), ('y', 20)])
            >>> print(sod)
            {'x': 10, 'y': 20}
        """
        items = [f"'{k}': {v}" for k, v in self.items()]
        return "{" + ", ".join(items) + "}"


def process_user_conferences_journals_json(full_json_c: str, full_json_j: str) -> tuple[dict, dict]:
    """Process user-defined conferences and journals JSON files.

    Notes:
        The structure of full_json_c follows the format
            {"publisher": {"conferences": {"abbr": {"names_abbr": [], "names_full": []}}}},
        while full_json_j adheres to the format
            {"publisher": {"journals": {"abbr": {"names_abbr": [], "names_full": []}}}}.
    """
    # Process user conferences JSON file
    json_dict = load_json_file(full_json_c)
    full_abbr_inproceedings_dict = {}

    # Try different possible keys for conferences section in JSON structure
    for flag in ["conferences", "Conferences", "CONFERENCES", "conference", "Conference", "CONFERENCE"]:
        full_abbr_inproceedings_dict = {p: json_dict[p].get(flag, {}) for p in json_dict}
        if full_abbr_inproceedings_dict:
            break

    # Flatten the nested dictionary structure to {abbr: value} format
    # Convert from {publisher: {abbr: data}} to {abbr: data}
    full_abbr_inproceedings_dict = {abbr: v[abbr] for v in full_abbr_inproceedings_dict.values() for abbr in v}
    # Standardize the structure to ensure consistent format
    # Extract only usefull information ("names_full" and "names_abbr")
    full_abbr_inproceedings_dict = {
        k: {"names_full": v.get("names_full", []), "names_abbr": v.get("names_abbr", [])}
        for k, v in full_abbr_inproceedings_dict.items()
    }

    # Process user journals JSON file
    json_dict = load_json_file(full_json_j)
    full_abbr_article_dict = {}

    # Try different possible keys for journals section in JSON structure
    for flag in ["journals", "Journals", "JOURNALS", "journal", "Journal", "JOURNAL"]:
        full_abbr_article_dict = {p: json_dict[p].get(flag, {}) for p in json_dict}
        if full_abbr_article_dict:
            break

    # Flatten the nested dictionary structure to {abbr: value} format
    # Convert from {publisher: {abbr: data}} to {abbr: data}
    full_abbr_article_dict = {abbr: v[abbr] for v in full_abbr_article_dict.values() for abbr in v}
    # Standardize the structure to ensure consistent format
    # Extract only usefull information ("names_full" and "names_abbr")
    full_abbr_article_dict = {
        k: {"names_full": v.get("names_full", []), "names_abbr": v.get("names_abbr", [])}
        for k, v in full_abbr_article_dict.items()
    }

    # Return both processed dictionaries
    return full_abbr_inproceedings_dict, full_abbr_article_dict


class CheckAcronymAbbrAndFullDict:
    """Checker for acronym, abbreviation and full form dictionaries.

    Validates and processes dictionary data containing acronyms with their
    corresponding abbreviations and full forms.

    Attributes:
        names_abbr (str): Key name for abbreviations in the dictionary.
        names_full (str): Key name for full forms in the dictionary.
    """

    def __init__(self, names_abbr: str = "names_abbr", names_full: str = "names_full") -> None:
        """Initializes the checker with field names.

        Args:
            names_abbr: Key name for abbreviations, defaults to "names_abbr".
            names_full: Key name for full forms, defaults to "names_full".
        """
        self.names_abbr = names_abbr
        self.names_full = names_full

    def length_dupicate_match(
        self, dict_data: dict[str, dict[str, list[str]]]
    ) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
        """Performs comprehensive validation on dictionary data.

        Executes three validation steps: length validation, duplicate checking,
        and mutual pattern matching.

        Args:
            dict_data: Dictionary containing acronym data with abbreviations
                      and full forms.

        Returns:
            tuple: Validated dictionary and list of acronyms with matches.
        """
        dict_data = self._validate_length(dict_data)
        dict_data = self._check_duplicate(dict_data)

        # Check for matching patterns in both abbreviations and full forms
        dict_data, abbr_matches = self._mutually_check_match(dict_data, self.names_abbr)
        dict_data, full_matches = self._mutually_check_match(dict_data, self.names_full)
        matches = sorted(set(abbr_matches).union(full_matches))
        return dict_data, matches

    def _validate_length(self, data_dict: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
        """Validates that each acronym has equal number of abbreviations and full forms.

        Args:
            data_dict: Input dictionary to validate.

        Returns:
            dict: Dictionary with only entries having equal length lists.
        """
        valid_data = {}
        for acronym, value_dict in data_dict.items():
            names_abbr = value_dict.get(self.names_abbr, [])
            names_full = value_dict.get(self.names_full, [])

            if len(names_abbr) != len(names_full):
                print(
                    f"Length mismatch in '{acronym}': {len(names_abbr)} abbreviations vs {len(names_full)} full forms"
                )
            else:
                valid_data[acronym] = value_dict
        return valid_data

    def _check_duplicate(self, data_dict: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
        """Checks for duplicate abbreviations or full forms across all acronyms.

        Args:
            data_dict: Input dictionary to check for duplicates.

        Returns:
            dict: Dictionary with duplicate entries removed.
        """
        valid_data = {}
        seen_abbrs = set()
        seen_fulls = set()

        for acronym, values in data_dict.items():
            has_duplicate = False

            # Check for duplicate abbreviations
            abbrs_lower = {abbr.lower() for abbr in values.get(self.names_abbr, [])}
            for abbr in abbrs_lower:
                if abbr in seen_abbrs:
                    print(f"Duplicate abbreviation '{abbr}' found in '{acronym}'")
                    has_duplicate = True
                else:
                    seen_abbrs.add(abbr)

            # Check for duplicate full forms
            fulls_lower = {full.lower() for full in values.get(self.names_full, [])}
            for full in fulls_lower:
                if full in seen_fulls:
                    print(f"Duplicate full form '{full}' found in '{acronym}'")
                    has_duplicate = True
                else:
                    seen_fulls.add(full)

            if not has_duplicate:
                valid_data[acronym] = values

        return valid_data

    def _mutually_check_match(self, data_dict: dict, key_type: str) -> tuple[dict, list[str]]:
        """Checks for exact matches in abbreviations or full forms between different acronyms.

        Args:
            data_dict: Dictionary to check for mutual matches.
            key_type: Type of key to check ("names_abbr" or "names_full").

        Returns:
            tuple: Validated dictionary and list of acronyms with matches.
        """
        valid_data = {}
        matches_acronyms = []
        acronyms_bak = sorted(data_dict.keys())

        for acronyms in [acronyms_bak, acronyms_bak[::-1]]:
            for i, main_acronym in enumerate(acronyms):
                # Normalize items: lowercase and remove parentheses
                main_items = [
                    item.lower().replace("(", "").replace(")", "") for item in data_dict[main_acronym].get(key_type, [])
                ]

                # Create exact match patterns
                patterns = [re.compile(f"^{item}$") for item in main_items]

                matches_found = []

                # Compare with other acronyms
                for other_acronym in acronyms[i + 1 :]:
                    other_items = [
                        item.lower().replace("(", "").replace(")", "")
                        for item in data_dict[other_acronym].get(key_type, [])
                    ]

                    # Find matching items
                    matching_items = [item for item in other_items if any(pattern.match(item) for pattern in patterns)]

                    if matching_items:
                        matches_found.append([main_acronym, other_acronym, matching_items])
                        matches_acronyms.append([main_acronym, other_acronym])

                if matches_found:
                    print(f"Found matches in {key_type}: {matches_found}")
                else:
                    valid_data[main_acronym] = data_dict[main_acronym]

        matches_acronyms = sorted({item for sublist in matches_acronyms for item in sublist})
        return valid_data, matches_acronyms

    def compare_and_return_only_in_new(self, json_old: dict, json_new: dict) -> dict:
        """Compares old and new JSON data to find newly added items.

        Args:
            json_old: Old JSON data as dictionary.
            json_new: New JSON data as dictionary.

        Returns:
            dict: Dictionary containing keys that only exist in new data.
        """
        # Find keys that only exist in new JSON
        keys_only_in_new = sorted(set(json_new.keys()) - set(json_old.keys()))
        new_only_data = {key: json_new[key] for key in keys_only_in_new}

        # Find common keys between old and new JSON
        common_keys = set(json_old.keys()) & set(json_new.keys())

        # Check each common key for new items using pattern matching
        for key in sorted(common_keys):
            for flag in [self.names_full]:
                old_items = [item.lower() for item in json_old[key][flag]]
                old_items = [item.replace("(", "").replace(")", "") for item in old_items]

                new_items = [item.lower() for item in json_new[key][flag]]
                new_items = [item.replace("(", "").replace(")", "") for item in new_items]

                self._old_match_new(json_old, key, flag, old_items, new_items)

        # Return keys that only exist in new data
        return new_only_data

    @staticmethod
    def _old_match_new(json_old: dict, key: str, flag: str, old_items: list[str], new_items: list[str]) -> None:
        """Compares old and new items for a specific key and flag.

        Args:
            json_old: Old JSON data.
            key: Current acronym key being processed.
            flag: Field type being checked ("names_abbr" or "names_full").
            old_items: Normalized items from old data.
            new_items: Normalized items from new data.
        """
        # Convert to regex patterns
        patterns = [re.compile(f"^{item}$") for item in old_items]

        unmatched = []
        for new_item in new_items:
            if (new_item not in old_items) and (not any(p.match(new_item) for p in patterns)):
                unmatched.append(new_item)

        if unmatched:
            print(f"\nManually handle - Key: {key}")
            print(f"Old data: {json_old[key][flag]}")
            print(f"New data: {unmatched}")
