from datetime import datetime
from typing import Optional, Dict

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBasePaginatedResponse
from thestage.services.clients.thestage_api.dtos.frontend_status import FrontendStatusDto
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.clients.thestage_api.dtos.instance_detected_gpus import InstanceDetectedGpusDto
from thestage.services.clients.thestage_api.dtos.enums.cpu_type import InstanceCpuType


class SelfHostedInstanceDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    slug: Optional[str] = Field(None, alias='slug')
    cpu_type: Optional[InstanceCpuType] = Field(InstanceCpuType.UNKNOWN, alias='cpuType')
    cpu_cores: Optional[int] = Field(None, alias='cpuCores')
    detected_gpus: Optional[InstanceDetectedGpusDto] = Field(None, alias='detectedGpus')
    frontend_status: Optional[FrontendStatusDto] = Field(None, alias='frontendStatus')
    ip_address: Optional[str] = Field(None, alias='ipAddress')


class SelfHostedInstanceListResponse(TheStageBasePaginatedResponse):
    paginated_list: Optional[PaginatedEntityList[SelfHostedInstanceDto]] = Field(None, alias='selfHostedInstanceList')


class SelfHostedRentedItemResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    selfhosted_instance: Optional[SelfHostedInstanceDto] = Field(None, alias='selfhostedInstance')


class SelfHostedRentedRentedBusinessStatusMapperResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    selfhosted_instance_business_status_map: Dict[str, str] = Field(default={}, alias='selfhostedInstanceBusinessStatusMap')
