# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Core Source imports
from core_pagination.pagination_dtos import PaginationDto
from core_pagination.pagination_tos import PaginationQueryParams, PaginationTo
from core_pagination.pagination_types import Pagination
from core_utils_file.data_utils import list_mapping

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "paginate_dto",
    "paginate_to",
    "pagination_params_from_rest_to_dto",
    "pagination_from_dto_to_rest",
    "pagination_from_rest_to_dto",
    "pagination_from_dict_to_rest",
]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                               Data Model Transformers                                                #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

GenericTo = TypeVar("GenericTo")
GenericDto = TypeVar("GenericDto")


def paginate_dto(
    data: List[GenericDto], pagination: Pagination, total: Optional[int] = None
) -> PaginationDto[GenericDto]:
    return PaginationDto(data=data, page=pagination.page, per_page=pagination.per_page, total=total or len(data))


def paginate_to(data: List[GenericTo], pagination: Pagination, total: Optional[int] = None) -> PaginationTo[GenericTo]:
    return PaginationTo(data=data, page=pagination.page, per_page=pagination.per_page, total=total or len(data))


def pagination_params_from_rest_to_dto(data: PaginationQueryParams) -> Pagination:
    return Pagination(page=data.page, per_page=data.per_page)


def pagination_from_dto_to_rest(
    data: PaginationDto[GenericDto], mapper: Callable[[GenericDto], GenericTo]
) -> PaginationTo[GenericTo]:
    return PaginationTo(
        page=data.page, per_page=data.per_page, total=data.total, data=list_mapping(mapper=mapper, values=data.data)
    )


def pagination_from_rest_to_dto(
    data: PaginationTo[GenericTo], mapper: Callable[[GenericTo], GenericDto]
) -> PaginationDto[GenericDto]:
    return PaginationDto(
        page=data.page, per_page=data.per_page, total=data.total, data=list_mapping(mapper=mapper, values=data.data)
    )


def pagination_from_dict_to_rest(
    data: Dict[str, Any], mapper: Callable[[Dict[str, Any]], GenericTo]
) -> PaginationTo[GenericTo]:
    return PaginationTo(
        page=data["page"],
        per_page=data["perPage"],
        total=data["total"],
        data=list_mapping(mapper=mapper, values=data["data"]),
    )
