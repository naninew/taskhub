# [Ngày 6] Generic paginated response schema

from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
