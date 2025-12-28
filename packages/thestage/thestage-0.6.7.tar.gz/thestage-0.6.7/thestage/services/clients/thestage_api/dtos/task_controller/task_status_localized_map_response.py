from typing import Dict

from pydantic import Field

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class TaskStatusLocalizedMapResponse(TheStageBaseResponse):
    taskStatusMap: Dict[str, str] = Field(default={}, alias='taskStatusMap')
