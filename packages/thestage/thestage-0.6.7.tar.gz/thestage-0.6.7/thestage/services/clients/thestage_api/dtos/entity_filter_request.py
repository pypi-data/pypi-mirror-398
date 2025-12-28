from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from thestage.entities.enums.order_direction_type import OrderDirectionType


class EntityFilterRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    orderByField: Optional[str] = Field(None, alias='orderByField')
    orderByDirection: Optional[OrderDirectionType] = Field(None, alias='orderByDirection')
    page: Optional[int] = Field(None, alias='page')
    limit: Optional[int] = Field(None, alias='limit')
