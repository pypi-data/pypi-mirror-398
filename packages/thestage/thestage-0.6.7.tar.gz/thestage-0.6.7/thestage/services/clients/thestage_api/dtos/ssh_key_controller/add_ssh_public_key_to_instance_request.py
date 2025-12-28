from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class AddSshPublicKeyToInstanceRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    instanceRentedPublicId: str = Field(None, alias='instanceRentedPublicId')
    sshPublicKeyPublicId: str = Field(None, alias='sshPublicKeyPublicId')
