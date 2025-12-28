from typing import Optional, List

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.logging.dto.log_message import LogMessage


class LogPollingResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    logs: Optional[List[LogMessage]] = Field(None, alias='logs')
    lastLogId: Optional[str] = Field(None, alias='lastLogId')
    lastLogTimestamp: Optional[str] = Field(None, alias='lastLogTimestamp')
