from pydantic import Field, ConfigDict, BaseModel


class AddSshKeyToUserRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    sshKey: str = Field(None, alias='sshKey')
    note: str = Field(None, alias='note')
