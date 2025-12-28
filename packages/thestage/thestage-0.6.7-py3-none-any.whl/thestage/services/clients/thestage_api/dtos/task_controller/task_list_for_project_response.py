
from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.task.dto.task_dto import TaskDto


class TaskListForProjectResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    tasks: PaginatedEntityList[TaskDto] = Field(None, alias='tasks')
