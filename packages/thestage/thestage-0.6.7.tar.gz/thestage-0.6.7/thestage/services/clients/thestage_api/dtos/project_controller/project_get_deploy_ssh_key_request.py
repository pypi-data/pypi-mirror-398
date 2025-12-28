from pydantic import Field, ConfigDict, BaseModel


class ProjectGetDeploySshKeyRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    projectPublicId: str = Field(None, alias='projectPublicId')
    projectSlug: str = Field(None, alias='projectSlug')
