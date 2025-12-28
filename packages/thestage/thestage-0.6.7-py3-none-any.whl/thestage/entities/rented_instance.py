from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RentedInstanceEntity(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

    public_id: Optional[str] = Field(None, alias='ID')
    slug: Optional[str] = Field(None, alias='NAME')
    status: Optional[str] = Field(None, alias='STATUS')
    cpu_type: Optional[str] = Field(None, alias='CPU TYPE')
    cpu_cores: Optional[str] = Field(None, alias='CPU CORES')
    gpu_type: Optional[str] = Field(None, alias='GPU TYPE')
    ip_address: Optional[str] = Field(None, alias='IP ADDRESS')
