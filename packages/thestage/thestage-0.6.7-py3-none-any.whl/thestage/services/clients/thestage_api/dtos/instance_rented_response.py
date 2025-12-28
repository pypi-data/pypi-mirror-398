from typing import Optional, Dict

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.frontend_status import FrontendStatusDto
from thestage.services.clients.thestage_api.dtos.base_response import TheStageBasePaginatedResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.clients.thestage_api.dtos.enums.gpu_name import InstanceGpuType
from thestage.services.clients.thestage_api.dtos.enums.cpu_type import InstanceCpuType


class InstanceRentedDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    slug: Optional[str] = Field(None, alias='slug')
    cpu_type: Optional[InstanceCpuType] = Field(InstanceCpuType.UNKNOWN, alias='cpuType')
    cpu_cores: Optional[int] = Field(None, alias='cpuCores')
    gpu_type: Optional[InstanceGpuType] = Field(InstanceGpuType.UNKNOWN, alias='gpuType')
    frontend_status: Optional[FrontendStatusDto] = Field(None, alias='frontendStatus')
    ip_address: Optional[str] = Field(None, alias='ipAddress')
    host_username: Optional[str] = Field(None, alias='hostUsername')


class InstanceRentedListResponse(TheStageBasePaginatedResponse):
    paginated_list: Optional[PaginatedEntityList[InstanceRentedDto]] = Field(None, alias='paginatedEntityList')


class InstanceRentedItemResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    instance_rented: Optional[InstanceRentedDto] = Field(None, alias='instanceRented')


class InstanceRentedBusinessStatusMapperResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    instance_rented_business_status_map: Dict[str, str] = Field(default={}, alias='instanceRentedBusinessStatusMap')
