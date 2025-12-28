from typing import Optional, List

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest


class GetInferenceSimulatorRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    publicId: Optional[str] = Field(None, alias='publicId')
    slug: Optional[str] = Field(None, alias='slug')
