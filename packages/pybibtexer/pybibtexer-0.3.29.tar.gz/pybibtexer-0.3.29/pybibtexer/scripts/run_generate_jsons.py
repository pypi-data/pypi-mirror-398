import os
import re

from ..main.utils import CheckAcronymAbbrAndFullDict, process_user_conferences_journals_json
from ..utils.utils import load_json_file, save_to_json


def run_generate_jsons(
    default_full_json_c: str,
    default_full_json_j: str,
    full_biblatex: str,
    user_full_json_c: str,
    user_full_json_j: str,
    merge_json: bool = False,
) -> None:
    """Execute the JSON generation process for conferences and journals.

    Args:
        default_full_json_c: Path to the default conferences JSON file.
        default_full_json_j: Path to the default journals JSON file.
        full_biblatex: Path to the BibLaTeX source file.
        user_full_json_c: Path to the user conferences JSON file.
        user_full_json_j: Path to the user journals JSON file.
        merge_json: Whether to merge and save JSON data. Defaults to False.

    Returns:
        None
    """
    GenerateDefaultJSONs(
        default_full_json_c,
        default_full_json_j,
        full_biblatex,
        user_full_json_c,
        user_full_json_j,
    ).run(merge_json)
    return None


class GenerateDefaultJSONs:
    """Generator for default JSON files from BibLaTeX source.

    This class handles the extraction and processing of conference and journal
    data from BibLaTeX files into structured JSON format.
    """

    def __init__(
        self,
        default_full_json_c: str,
        default_full_json_j: str,
        full_biblatex: str,
        user_full_json_c: str,
        user_full_json_j: str,
    ) -> None:
        """Initialize with file paths for JSON generation.

        Args:
            default_full_json_c: Path to default conferences JSON file.
            default_full_json_j: Path to default journals JSON file.
            full_biblatex: Path to BibLaTeX source file.
            user_full_json_c: Path to user conferences JSON file.
            user_full_json_j: Path to user journals JSON file.
        """
        # Expand environment variables and user home directory in file paths
        self.default_full_json_c = os.path.expandvars(os.path.expanduser(default_full_json_c))
        self.default_full_json_j = os.path.expandvars(os.path.expanduser(default_full_json_j))
        self.full_biblatex = os.path.expandvars(os.path.expanduser(full_biblatex))
        self.user_full_json_c = os.path.expandvars(os.path.expanduser(user_full_json_c))
        self.user_full_json_j = os.path.expandvars(os.path.expanduser(user_full_json_j))

    @staticmethod
    def _read_str(full_file: str) -> str:
        """Read file content as string.

        Args:
            full_file: Path to the file to read.

        Returns:
            Content of the file as string.
        """
        with open(full_file, encoding="utf-8", newline="\n") as file:
            content = file.read()
        return content

    def parse_bibtex_file(self, full_biblatex: str, entry_type: str = "article") -> dict[str, dict[str, list[str]]]:
        """Parse BibTeX file and extract conference or journal data.

        Args:
            full_biblatex: Path to the BibLaTeX file.
            entry_type: Type of entry to parse - 'article' or 'inproceedings'.

        Returns:
            Dictionary containing parsed conference or journal data.

        Raises:
            ValueError: If entry_type is not 'article' or 'inproceedings'.
        """
        if entry_type not in ["article", "inproceedings"]:
            raise ValueError("entry_type must be 'article' or 'inproceedings'")

        config = {
            "article": {
                "prefix": "J_",
                "pattern": r"@article\{(.*?),\s*([^@]*)\}",
                "full_field": "journaltitle",
                "abbr_field": "shortjournal",
            },
            "inproceedings": {
                "prefix": "C_",
                "pattern": r"@inproceedings\{(.*?),\s*([^@]*)\}",
                "full_field": "booktitle",
                "abbr_field": "eventtitle",
            },
        }

        cfg = config[entry_type]
        content = self._read_str(full_biblatex)
        entries = re.findall(cfg["pattern"], content, re.DOTALL)

        result_dict = {}
        for cite_key, entry_content in entries:
            # Process only entries with the specified prefix
            if not cite_key.startswith(cfg["prefix"]):
                continue

            # Extract full and abbreviation fields
            full_match = re.search(rf"{cfg['full_field']}\s*=\s*{{([^}}]*)}}", entry_content)
            abbr_match = re.search(rf"{cfg['abbr_field']}\s*=\s*{{([^}}]*)}}", entry_content)

            # For inproceedings, booktitle is required but eventtitle is optional
            if not full_match:
                continue

            full = full_match.group(1).strip()
            if abbr_match:
                abbr = abbr_match.group(1).strip()
            else:
                # Use full name as abbreviation if abbreviation field is missing
                abbr = full

            parts = cite_key.split("_")
            if len(parts) >= 3:
                key = parts[1]

                # Check if key already exists
                if key in result_dict:
                    existing_entry = result_dict[key]

                    # Only add if full name is not already present
                    if full not in existing_entry["names_full"]:
                        existing_entry["names_abbr"].append(abbr)
                        existing_entry["names_full"].append(full)
                else:
                    # New key - add to dictionary
                    result_dict[key] = {"names_abbr": [abbr], "names_full": [full]}

        return result_dict

    def run(self, merge_json: bool = False) -> None:
        """Execute the complete JSON generation pipeline.

        Args:
            merge_json: Whether to merge and save data to JSON files.
        """
        check = CheckAcronymAbbrAndFullDict()

        # ==================== Conference Data Processing ====================
        json_old_c = load_json_file(self.default_full_json_c)
        json_new_c = self.parse_bibtex_file(self.full_biblatex, "inproceedings")

        print("\n" + "*" * 9 + f" Checking existing conference data: `{self.default_full_json_c}` " + "*" * 9)
        json_old_c, _ = check.length_dupicate_match(json_old_c)

        print("\n" + "*" * 9 + f" Checking newly parsed conference data: `{self.full_biblatex}` " + "*" * 9)
        json_new_c, _ = check.length_dupicate_match(json_new_c)

        print("\n" + "*" * 9 + " Comparing existing conference data with newly parsed conference data " + "*" * 9)
        json_new_c = check.compare_and_return_only_in_new(json_old_c, json_new_c)

        # ==================== Journal Data Processing ====================
        json_old_j = load_json_file(self.default_full_json_j)
        json_new_j = self.parse_bibtex_file(self.full_biblatex, "article")

        print("\n" + "*" * 9 + f" Checking existing journal data: `{self.default_full_json_j}` " + "*" * 9)
        json_old_j, _ = check.length_dupicate_match(json_old_j)

        print("\n" + "*" * 9 + f" Checking newly parsed journal data: `{self.full_biblatex}` " + "*" * 9)
        json_new_j, _ = check.length_dupicate_match(json_new_j)

        print("\n" + "*" * 9 + " Comparing existing journal data with newly parsed journal data " + "*" * 9)
        json_new_j = check.compare_and_return_only_in_new(json_old_j, json_new_j)

        # ==================== User Data Integration ====================
        # Process user-specific conference and journal JSON files
        json_user_c, json_user_j = process_user_conferences_journals_json(self.user_full_json_c, self.user_full_json_j)

        # Check for duplicates in conferences data
        print("\n" + "*" * 9 + " Checking duplicates in conferences " + "*" * 9)
        c = {**json_new_c, **json_old_c, **json_user_c}  # Priority: user > old > new
        c, c_matches = check.length_dupicate_match(c)
        json_new_c = {k: v for k, v in json_new_c.items() if k not in c_matches}
        c = {**json_new_c, **json_old_c, **json_user_c}  # Priority: user > old > new

        # Check for duplicates in journals data
        print("\n" + "*" * 9 + " Checking duplicates in journals " + "*" * 9)
        j = {**json_new_j, **json_old_j, **json_user_j}  # Priority: user > old > new
        j, f_matches = check.length_dupicate_match(j)
        json_new_j = {k: v for k, v in json_new_j.items() if k not in f_matches}
        j = {**json_new_j, **json_old_j, **json_user_j}  # Priority: user > old > new

        # ==================== Data Merging and Saving ====================
        if merge_json:
            save_to_json(c, self.default_full_json_c)
            save_to_json(j, self.default_full_json_j)
            print("Data merging completed and saved")

        return None
