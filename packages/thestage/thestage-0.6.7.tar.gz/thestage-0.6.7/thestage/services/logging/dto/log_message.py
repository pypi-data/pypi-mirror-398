from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class LogMessage(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    logType: Optional[str] = Field(None, alias='logType')
    message: Optional[str] = Field(None, alias='message')
    timestamp: Optional[str] = Field(None, alias='timestamp')
    messageCode: Optional[int] = Field(None, alias='messageCode')
