from typing import Optional, List

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest


class DeployInferenceModelToSagemakerRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    modelPublicId: Optional[str] = Field(None, alias='modelPublicId')
    modelSlug: Optional[str] = Field(None, alias='modelSlug')
    arn: Optional[str] = Field(None, alias='arn')
