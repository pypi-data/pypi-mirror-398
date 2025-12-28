from typing import Optional

from pydantic import Field

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.task.dto.task_dto import TaskDto


class TaskViewResponse(TheStageBaseResponse):
    task: Optional[TaskDto] = Field(None, alias='task')
