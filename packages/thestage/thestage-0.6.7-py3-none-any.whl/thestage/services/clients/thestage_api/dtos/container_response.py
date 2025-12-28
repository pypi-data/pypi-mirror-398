from typing import Optional, List, Dict

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.docker_container_mapping import DockerContainerMappingDto
from thestage.services.clients.thestage_api.dtos.frontend_status import FrontendStatusDto
from thestage.services.clients.thestage_api.dtos.instance_rented_response import InstanceRentedDto
from thestage.services.clients.thestage_api.dtos.project_response import ProjectDto
from thestage.services.clients.thestage_api.dtos.selfhosted_instance_response import SelfHostedInstanceDto
from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse, TheStageBasePaginatedResponse
from thestage.services.clients.thestage_api.dtos.pagination_data import PaginationData


class DockerContainerDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    instance_rented: Optional[InstanceRentedDto] = Field(None, alias='instanceRented')
    selfhosted_instance: Optional[SelfHostedInstanceDto] = Field(None, alias='selfhostedInstance')
    project: Optional[ProjectDto] = Field(None, alias='project')
    system_name: Optional[str] = Field(None, alias='systemName')
    title: Optional[str] = Field(None, alias='title')
    slug: Optional[str] = Field(None, alias='slug')
    docker_image: Optional[str] = Field(None, alias='dockerImage')
    mappings: Optional[DockerContainerMappingDto] = Field(None, alias='mappings')

    frontend_status: Optional[FrontendStatusDto] = Field(None, alias='frontendStatus')


class DockerContainerPaginated(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    entities: List[DockerContainerDto] = Field(default_factory=list, alias='entities')
    current_page: Optional[int] = Field(None, alias='currentPage')
    last_page: Optional[bool] = Field(None, alias='lastPage')
    total_pages: Optional[int] = Field(None, alias='totalPages')
    pagination_data: Optional[PaginationData] = Field(None, alias='paginationData')


class DockerContainerViewResponse(TheStageBaseResponse):
    docker_container: Optional[DockerContainerDto] = Field(None, alias='dockerContainer')


class ContainerBusinessStatusMapperResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    docker_container_status_map: Dict[str, str] = Field(default={}, alias='dockerContainerStatusMap')
