from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class ProjectPushInferenceSimulatorModelRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulatorPublicId: Optional[str] = Field(None, alias='inferenceSimulatorPublicId')
    inferenceSimulatorSlug: Optional[str] = Field(None, alias='inferenceSimulatorSlug')
