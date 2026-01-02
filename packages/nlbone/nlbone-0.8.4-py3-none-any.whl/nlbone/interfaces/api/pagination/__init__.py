from typing import Generic, List, Optional, TypeVar

from fastapi import Depends
from pydantic import BaseModel

from .offset_base import PaginateRequest, PaginateResponse


def get_pagination(req: PaginateRequest = Depends(PaginateRequest)) -> PaginateRequest:
    return req


T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    total_count: Optional[int] = None
    total_page: Optional[int] = None
    data: List[T]
