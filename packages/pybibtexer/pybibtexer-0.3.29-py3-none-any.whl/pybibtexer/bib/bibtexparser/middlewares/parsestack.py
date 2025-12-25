from .middleware import Middleware


def default_parse_stack(allow_inplace_modification: bool = True) -> list[Middleware]:
    """Give the default parse stack to be applied after splitting, if not specified otherwise."""
    return []


def default_unparse_stack(allow_inplace_modification: bool = False) -> list[Middleware]:
    """Give the default unparse stack to be applied before writing, if not specified otherwise."""
    return []
