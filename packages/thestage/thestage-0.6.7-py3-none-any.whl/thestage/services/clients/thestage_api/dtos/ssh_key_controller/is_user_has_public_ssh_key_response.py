from typing import Optional

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class IsUserHasSshPublicKeyResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    isUserHasPublicKey: bool = Field(None, alias='isUserHasPublicKey')
    sshKeyPairPublicId: Optional[str] = Field(None, alias='sshKeyPairPublicId')
