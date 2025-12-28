from typing import List, Optional

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.container_response import DockerContainerDto
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.clients.thestage_api.dtos.pagination_data import PaginationData

class DockerContainerListResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    paginatedList: PaginatedEntityList[DockerContainerDto] = Field(None, alias='paginatedList')
