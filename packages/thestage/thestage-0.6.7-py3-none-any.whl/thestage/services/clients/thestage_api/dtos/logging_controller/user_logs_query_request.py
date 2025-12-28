from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class UserLogsQueryRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    containerPublicId: Optional[str] = Field(None, alias='containerPublicId')
    taskPublicId: Optional[str] = Field(None, alias='taskPublicId')
    inferenceSimulatorPublicId: Optional[str] = Field(None, alias='inferenceSimulatorPublicId')
    limit: Optional[int] = Field(None, alias='limit')
    ascendingOrder: Optional[bool] = Field(None, alias='ascendingOrder')
