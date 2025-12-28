from typing import Dict

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBasePaginatedResponse


class InferenceSimulatorStatusMapperResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    inference_simulator_status_map: Dict[str, str] = Field(default={}, alias='inferenceSimulatorStatusMap')
