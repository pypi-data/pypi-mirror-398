from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class ProjectRunTaskRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    projectPublicId: str = Field(None, alias='projectPublicId')
    dockerContainerPublicId: str = Field(None, alias='dockerContainerPublicId')
    commitHash: Optional[str] = Field(None, alias='commitHash')
    runCommand: str = Field(None, alias='runCommand')
    taskTitle: Optional[str] = Field(None, alias='taskTitle')
