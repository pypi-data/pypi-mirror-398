from typing import Any

from .library import Library
from .model import ImplicitComment


class MiddlewaresStrToLibrary:
    """Middlewares for converting a string to a library.

    Args:
        options (dict): Options for the middlewares.

    Attributes:
        is_display_implicit_comments (bool): Display implicit comments. Default is True.
    """

    def __init__(self, options: dict[str, Any]):
        self.is_display_implicit_comments = options.get("is_display_implicit_comments", True)

    def functions(self, library: Library) -> Library:
        # Display implicit comments
        if self.is_display_implicit_comments:
            other_blocks, implicit_comment_blocks = [], []
            for block in library.blocks:
                if isinstance(block, ImplicitComment):
                    implicit_comment_blocks.append(block)
                else:
                    other_blocks.append(block)

            library = Library(other_blocks)

            if implicit_comment_blocks:
                print(implicit_comment_blocks)

        return library
