import re

from ...library import Library
from ...model import Entry
from ..middleware import LibraryMiddleware
from ..utils import SKIP_WORD_IN_CITATION_KEY, generate_cite_key_prefix


class GenerateEntriesCiteKey(LibraryMiddleware):
    """Generate entries key of a library.

    The entry.key is also `Cite Key`.
    """

    # docstr-coverage: inherited
    def __init__(
        self,
        abbr_article_pattern_dict: dict,
        abbr_inproceedings_pattern_dict: dict,
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.abbr_article_pattern_dict = abbr_article_pattern_dict
        self.abbr_inproceedings_pattern_dict = abbr_inproceedings_pattern_dict

    # docstr-coverage: inherited
    def transform(self, library: Library) -> Library:
        library = super().transform(library)
        for entry in library.entries:
            generate_key = self.generate_cite_key(entry)
            while generate_key in [e.key for e in library.entries if e != entry]:
                generate_key = generate_key + "-a"
            entry.key = generate_key
        return library

    def generate_cite_key(self, entry: Entry) -> str:
        """Generate user citation key."""
        prefix = generate_cite_key_prefix(
            entry,
            self.abbr_article_pattern_dict,
            self.abbr_inproceedings_pattern_dict,
        )

        cite_key = self.generate_google_cite_key(entry)
        if prefix != "":
            cite_key = prefix + "_" + cite_key
        return cite_key

    @staticmethod
    def _obtain_family_name(author: str) -> str:
        """Obtain the family name of first author."""
        author = re.sub(r"\noopsort", "", author)
        author = re.sub("}{", " ", author)
        if re.search(r"\s+and\s+", author):  # Zhe Feng, Tianxi Li, Haifeng Xu and Fei Zhang
            author = re.split(r"\s+and\s+", author)[0]

        if re.search(r",", author):  # Zhe Feng, Tianxi Li, Haifeng Xu
            author = re.split(r",", author)[0]

        author = author.strip()

        if re.search(r"\s+", author):  # M. Li or Ming Li (given name family name)
            f_list = re.split(r"\s+", author)
            f_list = [f.strip() for f in f_list if len(f.strip()) != 0]
            family_name = f_list[-1]
        else:
            family_name = author
        return family_name

    def generate_google_cite_key(self, entry: Entry) -> str:
        """Generate google citation key."""
        author = entry["author"] if "author" in entry else ""
        family_name = self._obtain_family_name(author).lower()

        year = entry["year"] if "year" in entry else ""

        first_word_of_title = ""
        title = entry["title"] if "title" in entry else ""
        regex = re.compile(r"\\href{(.*)}{(.*)}")
        if mch := regex.search(title):
            title = mch.group(2)

        word_list = [w.lower() for w in re.split(r"\s+", title) if w.strip()]
        word_list = [re.sub(r"[^a-zA-Z0-9]", "", w) for w in word_list]
        for w in word_list:
            if w not in SKIP_WORD_IN_CITATION_KEY:
                first_word_of_title = w
                break

        citation_key = family_name + year + first_word_of_title
        return re.sub(r"[^a-zA-Z0-9]", "", citation_key)
