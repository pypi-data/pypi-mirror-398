from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class LogPollingRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    taskPublicId: Optional[str] = Field(None, alias='taskPublicId')
    inferenceSimulatorPublicId: Optional[str] = Field(None, alias='inferenceSimulatorPublicId')
    lastLogId: Optional[str] = Field(None, alias='lastLogId')
    dockerContainerPublicId: Optional[str] = Field(None, alias='dockerContainerPublicId')
    lastLogTimestamp: Optional[str] = Field(None, alias='lastLogTimestamp')
