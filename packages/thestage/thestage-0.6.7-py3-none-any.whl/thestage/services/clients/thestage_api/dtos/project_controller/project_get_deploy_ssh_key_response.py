from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class ProjectGetDeploySshKeyResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    publicKey: str = Field(None, alias='publicKey')
    privateKey: str = Field(None, alias='privateKey')
