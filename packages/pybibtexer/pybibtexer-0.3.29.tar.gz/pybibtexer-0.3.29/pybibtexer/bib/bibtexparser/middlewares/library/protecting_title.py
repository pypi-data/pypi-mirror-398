import string

from ...library import Library
from ..middleware import LibraryMiddleware


class ProtectTitleWithBracket(LibraryMiddleware):
    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

    # docstr-coverage: inherited
    def transform(self, library: Library) -> Library:
        library = super().transform(library)
        for entry in library.entries:
            if "title" in entry:
                entry["title"] = process_sentence_refined(entry["title"])
        return library

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return "protect_title_with_bracket"


def wrap_if_internal_capital_with_punctuation(word):
    if not isinstance(word, str) or len(word) <= 1:
        return word

    word_stripped = word.rstrip(string.punctuation)
    trailing_punct = word[len(word_stripped):]

    if len(word_stripped) <= 1:
        return word

    rest = word_stripped[1:]
    if any(c.isupper() for c in rest):
        return "{" + word_stripped + "}" + trailing_punct

    return word


def process_sentence_refined(sentence):
    words = sentence.split()
    processed_words = []

    for word in words:
        processed_word = wrap_if_internal_capital_with_punctuation(word)
        processed_words.append(processed_word)

    return ' '.join(processed_words)
