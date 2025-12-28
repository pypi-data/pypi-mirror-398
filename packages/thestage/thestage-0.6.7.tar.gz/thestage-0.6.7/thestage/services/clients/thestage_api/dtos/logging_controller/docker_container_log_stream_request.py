from pydantic import Field, ConfigDict, BaseModel


class DockerContainerLogStreamRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    dockerContainerId: int = Field(None, alias='dockerContainerId')
