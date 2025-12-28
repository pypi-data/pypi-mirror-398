from typing import Optional

from pydantic import BaseModel, Field


class PaginationData(BaseModel):
    current_page: Optional[int] = Field(None, alias='currentPage')
    limit: Optional[int] = Field(None, alias='limit')
    total_pages: Optional[int] = Field(None, alias='totalPages')
    objects_count: Optional[int] = Field(None, alias='objectsCount')
