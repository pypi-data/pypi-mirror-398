# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Final, NamedTuple

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["PAGINATION_PAGE", "PAGINATION_PER_PAGE", "Pagination"]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      Data types                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


PAGINATION_PAGE: Final[int] = 1
PAGINATION_PER_PAGE: Final[int] = 15


class Pagination(NamedTuple):
    """
    Pagination parameters.
    """

    page: int = 0
    per_page: int = 0
