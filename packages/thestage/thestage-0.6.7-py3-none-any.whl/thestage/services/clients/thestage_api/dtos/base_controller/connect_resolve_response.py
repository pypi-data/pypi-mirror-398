from typing import Optional, List

from pydantic import Field, BaseModel

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.frontend_status import FrontendStatusDto
from thestage.services.task.dto.task_dto import TaskDto


class EntityMatchData(BaseModel):
    publicId: str = Field(alias='publicId')
    frontendStatus: FrontendStatusDto = Field(alias='frontendStatus')
    canConnect: bool = Field(alias='canConnect')
    canDownloadUploadOnContainer: bool = Field(alias='canDownloadUploadOnContainer')
    matchedField: Optional[str] = Field(None, alias='matchedField')


class ConnectResolveOptionsResponse(TheStageBaseResponse):
    taskMatchData: List[EntityMatchData] = Field(None, alias='taskMatchData')
    dockerContainerMatchData: List[EntityMatchData] = Field(None, alias='dockerContainerMatchData')
    instanceRentedMatchData: List[EntityMatchData] = Field(None, alias='instanceRentedMatchData')
    selfhostedInstanceMatchData: List[EntityMatchData] = Field(None, alias='selfhostedInstanceMatchData')
