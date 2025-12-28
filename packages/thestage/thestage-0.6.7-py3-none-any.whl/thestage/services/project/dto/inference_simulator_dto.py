from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

class InferenceSimulatorDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias="publicId")
    slug: Optional[str] = Field(None, alias="slug")
    status: Optional[str] = Field(None, alias="status")
    http_endpoint: Optional[str] = Field(None, alias="httpEndpoint")
    grpc_endpoint: Optional[str] = Field(None, alias="grpcEndpoint")
    metrics_endpoint: Optional[str] = Field(None, alias="metricsEndpoint")
    qlip_serve_metadata: Optional[Dict[str, Any]] = Field(None, alias="qlipServeMetadata")
    created_at: Optional[str] = Field(None, alias="createdAt")
