from typing import Dict

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBasePaginatedResponse


class InferenceSimulatorModelStatusMapperResponse(TheStageBasePaginatedResponse):
    model_config = ConfigDict(use_enum_values=True)

    inference_simulator_model_status_map: Dict[str, str] = Field(default={}, alias='inferenceSimulatorModelStatusMap')
