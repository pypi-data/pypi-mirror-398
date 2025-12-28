from typing import Optional, List

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest


class InferenceSimulatorModelListForProjectRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    entityFilterRequest: EntityFilterRequest = Field(None, alias='entityFilterRequest')
    projectPublicId: Optional[str] = Field(None, alias='projectPublicId')
    projectSlug: Optional[str] = Field(None, alias='projectSlug')
    statuses: Optional[List[str]] = None