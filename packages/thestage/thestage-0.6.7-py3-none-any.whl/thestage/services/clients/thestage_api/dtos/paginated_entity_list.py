from typing import List, Optional, Any, Generic, TypeVar

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.pagination_data import PaginationData

T = TypeVar('T')

class PaginatedEntityList(BaseModel, Generic[T]):
    entities: List[T] = Field(default_factory=list, alias='entities')
    pagination_data: Optional[PaginationData] = Field(None, alias='paginationData')
