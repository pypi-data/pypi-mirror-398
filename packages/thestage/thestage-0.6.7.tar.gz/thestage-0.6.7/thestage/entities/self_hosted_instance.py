from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SelfHostedInstanceEntity(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
    )

    public_id: Optional[str] = Field(None, alias='ID')
    slug: Optional[str] = Field(None, alias='NAME')
    status: Optional[str] = Field(None, alias='STATUS')
    cpu_type: Optional[str] = Field(str, alias='CPU_TYPE')
    cpu_cores: Optional[int] = Field(None, alias='CPU_CORES')
    gpu_type: Optional[str] = Field(str, alias='GPU_TYPE')
    ip_address: Optional[str] = Field(None, alias='IP_ADDRESS')
