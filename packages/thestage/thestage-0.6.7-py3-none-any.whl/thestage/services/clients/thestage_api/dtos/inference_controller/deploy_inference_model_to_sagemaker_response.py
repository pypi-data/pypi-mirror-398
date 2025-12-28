from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class DeployInferenceModelToSagemakerResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)
    modelId: str = Field(None, alias='modelId')
    ecrImageUrl: str = Field(None, alias='ecrImageUrl')
    s3ArtifactsUrl: str = Field(None, alias='s3ArtifactsUrl')


