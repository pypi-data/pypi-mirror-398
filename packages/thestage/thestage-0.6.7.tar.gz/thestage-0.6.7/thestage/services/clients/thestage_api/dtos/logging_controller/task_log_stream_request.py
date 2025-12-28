from pydantic import Field, ConfigDict, BaseModel


class TaskLogStreamRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    taskId: int = Field(None, alias='taskId')
