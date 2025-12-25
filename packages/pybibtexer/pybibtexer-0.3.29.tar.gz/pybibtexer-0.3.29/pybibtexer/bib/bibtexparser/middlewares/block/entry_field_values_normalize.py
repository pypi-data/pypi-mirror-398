import logging
import re

from ...library import Library
from ...model import Block, Entry, Field
from ..middleware import BlockMiddleware
from ..utils import SKIP_WORD_IN_CITATION_KEY

logger = logging.getLogger(__name__)


class NormalizeEntryFieldValues(BlockMiddleware):
    """Normalize some field values (journal and booktitle) to upper case."""

    def __init__(
        self,
        field_keys: list[str] = ["journal", "booktitle"],
        title_lower_upper: str = "upper",
        allow_inplace_modification: bool = True,
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self._field_keys = field_keys
        self.title_lower_upper = title_lower_upper

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Entry:
        seen_normalized_keys: set[str] = set()
        new_fields_dict: dict[str, Field] = {}
        for field in entry.fields:
            if self.title_lower_upper == "upper":
                normalized_key: str = field.key.upper()
            elif self.title_lower_upper == "lower":
                normalized_key: str = field.key.lower()
            else:
                normalized_key: str = field.key.upper()
            # if the normalized key is already present, apply "last one wins"
            # otherwise preserve insertion order
            # if a key is overwritten, emit a detailed warning
            # if performance is a concern, we could emit a warning with only {entry.key}
            # to remove "seen_normalized_keys" and this if statement
            if normalized_key in seen_normalized_keys:
                logger.warning(
                    f"NormalizeFieldKeys: in entry '{entry.key}': "
                    + f"duplicate normalized key '{normalized_key}' "
                    + f"(original '{field.key}'); overriding previous value"
                )
            seen_normalized_keys.add(normalized_key)
            field.key = normalized_key
            new_fields_dict[normalized_key] = field

        new_fields: list[Field] = list(new_fields_dict.values())
        entry.fields = new_fields

        return entry


class AddUrlToFieldValueInEntry(BlockMiddleware):
    """Add url link to title."""

    # docstr-coverage: inherited
    def __init__(self, field_key: str, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.field_key = field_key

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        url = ""
        if "doi" in entry:
            url = entry["doi"]
            if (len(url) != 0) and (not re.match(r"https*://", url)):
                url = f"https://doi.org/{url}"
        elif "url" in entry:
            url = entry["url"]

        if (len(url) != 0) and self.field_key in entry:
            entry[self.field_key] = r"\href{" + str(url) + "}" + "{" + entry[self.field_key] + "}"
        return entry


class NormalizeFieldValuesInEntry(BlockMiddleware):
    """Sentence field values."""

    # docstr-coverage: inherited
    def __init__(self, field_key: str, sentence_title: str, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

        self.field_key = field_key
        self.sentence_title = sentence_title

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if self.field_key in entry:
            text = entry[self.field_key]
            # Convert to lowercase if all of the following conditions are met:
            # 1. Contains at least one letter character (to exclude pure numbers/symbols)
            # 2. All letters are uppercase (to exclude mixed case or already lowercase text)
            # 3. Contains multiple words (to preserve single acronyms/abbreviations)
            if bool(re.search(r"[A-Za-z]", text)) and text.isupper() and len(text.split(" ")) > 1:
                entry[self.field_key] = text.lower()

            if self.sentence_title == "sentence":
                entry[self.field_key] = self.generate_standard_sentence_case(entry[self.field_key])
            if self.sentence_title == "title":
                entry[self.field_key] = self.generate_standard_title_case(entry[self.field_key])
        return entry

    @staticmethod
    def __upper_or_lower_first_letter(input_str: str, flag: str) -> str:
        """Upper or lower first letter.

        Check whether the first is in the a-zA-Z and then UPPER or LOWER it.
        flag = upper
        Input: about; $food; About; aBout
        Output: About; $food; About; ABout
        flag = lower
        Input: About; $food; about; ABout
        Output: about; $food; about; aBout
        """
        new_input_str = input_str.strip()
        if new_input_str and re.search(r"[a-zA-Z]", new_input_str[0]):
            if flag == "lower":
                new_input_str = new_input_str[0].lower() + new_input_str[1:]
            elif flag == "upper":
                new_input_str = new_input_str[0].upper() + new_input_str[1:]
            else:
                new_input_str = input_str
        return new_input_str

    def __lower_first_letter_and_others_not_contain_uppers(self, input_str: str) -> str:
        """Lower.

        Input: About; A; $about; ABOUT; aBOUT
        Output: about; a; $about; ABOUT; aBOUT
        """
        new_input_str = input_str.strip()
        if new_input_str and (not re.search(r"[A-Z]", new_input_str[1:])):  # Others not contain upper letter
            input_str = self.__upper_or_lower_first_letter(input_str, "lower")  # Lower
        return input_str

    def __upper_first_letter_and_others_not_contain_uppers(self, input_str: str) -> str:
        """Upper.

        Input: about; a; $about; ABOUT; abOUT
        Output: About; A; $about; ABOUT; abOUT
        """
        new_input_str = input_str.strip()
        if new_input_str.lower() in SKIP_WORD_IN_CITATION_KEY:
            return new_input_str.lower()

        if new_input_str and (not re.search(r"[A-Z]", new_input_str[1:])):  # Others not contain upper letter
            input_str = self.__upper_or_lower_first_letter(input_str, "upper")  # upper
        return input_str

    def __generate_new_case_title(self, old_title: str, flag: str) -> str:
        """Generate new title."""
        old_list, new_list = re.split(r"\s+", old_title), []
        for i in range(len(old_list)):
            old_str = old_list[i]
            if re.search(r"-", old_str):
                temp_list, new_temp_list = re.split("-", old_str), []
                if i == 0:  # for the first element
                    new_temp_list = [self.__upper_or_lower_first_letter(temp_list[0], "upper")]
                    temp_list = temp_list[1:]
                for t in temp_list:
                    if len(t.strip()) == 1:
                        new_temp_list.append(t)  # not change
                    else:
                        if flag == "sentence":
                            new_temp_list.append(self.__lower_first_letter_and_others_not_contain_uppers(t))
                        elif flag == "title":
                            new_temp_list.append(self.__upper_first_letter_and_others_not_contain_uppers(t))
                        else:
                            pass
                new_list.append("-".join(new_temp_list))
            else:
                if i == 0:
                    new_list.append(self.__upper_or_lower_first_letter(old_str, "upper"))
                else:
                    if flag == "sentence":
                        new_list.append(self.__lower_first_letter_and_others_not_contain_uppers(old_str))
                    elif flag == "title":
                        new_list.append(self.__upper_first_letter_and_others_not_contain_uppers(old_str))
                    else:
                        pass
        return " ".join(new_list)

    def _generate_standard_title(self, title_content: str, flag: str) -> str:
        title_list, relative_flags = [title_content], []
        flags = [r":\s+", r"\s+-\s+", r"\s+--\s+", r"\s+—\s+", r"\s+——\s+", r"\s+–\s+", r"\s+––\s+"]
        for i in range(len(flags)):
            new_title_list = []
            for j in range(len(title_list)):
                temp_list = re.split(flags[i], title_list[j])
                new_title_list.extend(temp_list)
                if len(temp_list) > 1:
                    relative_flags[j:j] = [flags[i].replace(r"\s+", " ") for _ in range(len(temp_list) - 1)]
            title_list = new_title_list

        new_title = ""
        title_list = [self.__generate_new_case_title(t.strip(), flag) for t in title_list]
        for i in range(ll := len(title_list)):
            new_title = new_title + title_list[i]
            if i < (ll - 1):
                new_title = new_title + relative_flags[i]
        return new_title

    # --------- --------- --------- --------- --------- --------- --------- --------- --------- #
    def generate_standard_sentence_case(self, title_content: str) -> str:
        """Generate standard title.

        "Hello, world".upper() # HELLO WORLD
        "HELLO, WORLD".lower() # hello world
        "hello, world".capitalize() # Hello, world
        "hello, world".title() # Hello, World
        """
        return self._generate_standard_title(title_content, "sentence")

    # --------- --------- --------- --------- --------- --------- --------- --------- --------- #
    def generate_standard_title_case(self, title_content: str) -> str:
        """Generate standard title.

        "Hello, world".upper() # HELLO WORLD
        "HELLO, WORLD".lower() # hello world
        "hello, world".capitalize() # Hello, world
        "hello, world".title() # Hello, World
        """
        return self._generate_standard_title(title_content, "title")
