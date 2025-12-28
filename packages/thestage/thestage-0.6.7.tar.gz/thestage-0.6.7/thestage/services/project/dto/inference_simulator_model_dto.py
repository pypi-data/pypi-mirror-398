from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

class InferenceSimulatorModelDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    slug: Optional[str] = Field(None, alias='slug')
    status: Optional[str] = Field(None, alias='status')
    environment_metadata: Optional[Dict[str, Any]] = Field(None, alias='environmentMetadata')
    commit_hash: Optional[str] = Field(None, alias='commitHash')
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
