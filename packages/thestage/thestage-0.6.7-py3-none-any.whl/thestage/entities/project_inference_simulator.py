from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectInferenceSimulatorEntity(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    public_id: Optional[str] = Field(None, alias='ID')
    slug: Optional[str] = Field(None, alias='NAME')
    status: Optional[str] = Field(None, alias='STATUS')
    http_endpoint: Optional[str] = Field(None, alias="HTTP")
    grpc_endpoint: Optional[str] = Field(None, alias="GRPC")
    metrics_endpoint: Optional[str] = Field(None, alias="METRICS")
    started_at: Optional[str] = Field(None, alias='STARTED AT')
