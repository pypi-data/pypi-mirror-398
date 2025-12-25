# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Generic, List

# Internal libraries
from pydantic import Field

from core_common_data_types.base_data_types import BaseModelWithAlias

# Core Source imports
from core_common_data_types.type_definitions import GenericT
from core_pagination.pagination_types import PAGINATION_PAGE, PAGINATION_PER_PAGE

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["PaginationQueryParams", "PaginationTo"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                     Data Models                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class PaginationQueryParams(BaseModelWithAlias):
    """
    Request parameter for the pagination of the response.
    """

    page: int = Field(default=PAGINATION_PAGE, ge=1, description="The page number")
    per_page: int = Field(default=PAGINATION_PER_PAGE, ge=1, description="The number of items per page")


class PaginationTo(BaseModelWithAlias, Generic[GenericT]):
    """
    Pagination Transfer Object.
    """

    page: int = Field(..., description="The current page")
    per_page: int = Field(..., description="The requested number of items in page")
    total: int = Field(..., description="The total number of items")
    data: List[GenericT] = Field(..., description="The list of items")
