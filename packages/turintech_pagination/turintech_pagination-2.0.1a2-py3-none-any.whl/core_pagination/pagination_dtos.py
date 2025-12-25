# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Generic, List

from pydantic import Field
from pydantic.generics import GenericModel

# Core Source imports
from core_common_data_types.type_definitions import GenericT

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["PaginationDto"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                     Data Models                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class PaginationDto(GenericModel, Generic[GenericT]):
    """
    Pagination Data Transfer Object.
    """

    page: int = Field(description="The current page")
    per_page: int = Field(description="The requested number of items in page")
    total: int = Field(description="The total number of items")
    data: List[GenericT] = Field(description="The list of items")
