from pydantic import Field, ConfigDict, BaseModel


class IsUserHasSshPublicKeyRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    sshKey: str = Field(None, alias='sshKey')
