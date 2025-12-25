import re
from typing import Any

from ...bibtexbase.standardize_bib import MARKS_FLAGS
from ..model import Entry


def generate_cite_key_prefix(
    entry: Entry,
    abbr_article_pattern_dict: dict[str, Any],
    abbr_inporceedings_pattern_dict: dict[str, Any],
) -> str:
    prefix = generate_entry_abbr(entry.entry_type)

    if prefix.upper() in ["C", "J"]:
        prefix = generate_cite_key_prefix_c_j(entry, abbr_article_pattern_dict, abbr_inporceedings_pattern_dict)

    elif prefix == "D":
        if "url" in entry:
            if re.search(r"arxiv\.org", entry["url"]):
                prefix = "arXiv"
            elif re.search(r"biorxiv\.org", entry["url"]):
                prefix = "bioRxiv"
            elif re.search(r"ssrn\.", entry["url"]):
                prefix = "SSRN"
    return prefix


def generate_cite_key_prefix_c_j(
    entry: Entry,
    abbr_article_pattern_dict: dict[str, Any],
    abbr_inporceedings_pattern_dict: dict[str, Any],
) -> str:
    if entry.entry_type.lower() == "article":
        abbr_patterns = abbr_article_pattern_dict
        field_key = "journal"
        prefix = "J"
    elif entry.entry_type.lower() == "inproceedings":
        abbr_patterns = abbr_inporceedings_pattern_dict
        field_key = "booktitle"
        prefix = "C"
    else:
        return ""

    # Get field content for matching
    field_content = entry[field_key] if field_key in entry else ""
    if not field_content:
        return prefix

    # First matching attempt: exact lowercase match
    abbr_match = _find_abbreviation_match(field_content, abbr_patterns)
    if abbr_match:
        return f"{prefix}_{abbr_match}"

    # Second matching attempt: remove content in parentheses and try pattern match
    # 2024 IEEE congress on evolutionary computation (CEC)
    # 2024 IEEE congress on evolutionary computation
    field_content_clean = re.sub(r"\(.*\)", "", field_content).strip()
    if field_content_clean:
        abbr_match = _find_pattern_match(field_content_clean, abbr_patterns)
        if abbr_match:
            return f"{prefix}_{abbr_match}"

    # Third
    cite_key = entry.key
    if cite_key.startswith("J_") or cite_key.startswith("C_"):
        if (len(ll := cite_key.split("_")) == 3) and (ll[1] in abbr_patterns):
            return f"{prefix}_{ll[1]}"

    return prefix


def _find_abbreviation_match(content: str, patterns: dict[str, Any]) -> str:
    """Find abbreviation match using exact lowercase comparison.

    Args:
        content: Field content to match.
        patterns: Dictionary of abbreviation patterns.

    Returns:
        Matched abbreviation or empty string if no match.
    """
    content_lower = content.lower()
    for abbr, pattern_data in patterns.items():
        if content_lower in pattern_data["names"]:
            return abbr
    return ""


def _find_pattern_match(content: str, patterns: dict[str, Any]) -> str:
    """Find abbreviation match using regex pattern matching.

    Args:
        content: Field content to match.
        patterns: Dictionary of abbreviation patterns.

    Returns:
        Matched abbreviation or empty string if no match.
    """
    matches = []
    for abbr, pattern_data in patterns.items():
        if pattern_data["pattern"].match(content):
            matches.append(abbr)
            # TODO: match all?
            break

    # Handle multiple matches
    if len(matches) > 1:
        print(f"Multiple match: {matches} for {content}.")
        return matches[0]  # Return first match
    elif len(matches) == 1:
        return matches[0]

    return ""


def generate_entry_abbr(entry_type: str) -> str:
    """Generate abbr according to entry type.

    zotero item type:
        ['Journal Article', 'Conference Paper', 'Book', 'Book Section', 'Document', 'Manuscript', 'Report', 'Thesis',
         'Thesis']
    zotero export:
        ['article', 'inproceedings','book', 'incollection', 'misc', 'unpublished', 'techreport', 'phdthesis',
         'masterthesis']
    """
    entries = {k[0]: k[2] for k in MARKS_FLAGS if k[1] == "entry"}
    return entries.get(entry_type.lower(), "")


SKIP_WORD_IN_CITATION_KEY = [
    "a",
    "ab",
    "aboard",
    "about",
    "above",
    "across",
    "after",
    "against",
    "al",
    "along",
    "amid",
    "among",
    "an",
    "and",
    "anti",
    "around",
    "as",
    "at",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "besides",
    "between",
    "beyond",
    "but",
    "by",
    "d",
    "da",
    "das",
    "de",
    "del",
    "dell",
    "dello",
    "dei",
    "degli",
    "della",
    "dell",
    "delle",
    "dem",
    "den",
    "der",
    "des",
    "despite",
    "die",
    "do",
    "down",
    "du",
    "during",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "el",
    "en",
    "et",
    "except",
    "for",
    "from",
    "gli",
    "i",
    "il",
    "in",
    "inside",
    "into",
    "is",
    "l",
    "la",
    "las",
    "le",
    "les",
    "like",
    "lo",
    "los",
    "near",
    "nor",
    "of",
    "off",
    "on",
    "onto",
    "or",
    "over",
    "past",
    "per",
    "plus",
    "round",
    "save",
    "since",
    "so",
    "some",
    "sur",
    "than",
    "the",
    "through",
    "to",
    "toward",
    "towards",
    "un",
    "una",
    "unas",
    "under",
    "underneath",
    "une",
    "unlike",
    "uno",
    "unos",
    "until",
    "up",
    "upon",
    "versus",
    "via",
    "von",
    "while",
    "with",
    "within",
    "without",
    "yet",
    "zu",
    "zum",
]
