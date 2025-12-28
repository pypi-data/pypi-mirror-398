from typing import Optional, List

from pydantic import Field, ConfigDict, BaseModel

from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto


class GetInferenceSimulatorResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    inferenceSimulator: Optional[InferenceSimulatorDto] = Field(None, alias='inferenceSimulator')


