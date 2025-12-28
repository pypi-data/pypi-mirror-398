from typing import Optional, List

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.task.dto.task_dto import TaskDto


class ProjectRunTaskResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    task: TaskDto = Field(None, alias='task')
    tasksInQueue: Optional[List[TaskDto]] = Field(None, alias='tasksInQueue')
