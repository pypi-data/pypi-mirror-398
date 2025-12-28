from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto


class ProjectStartInferenceSimulatorResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulator: InferenceSimulatorDto = Field(None, alias='inferenceSimulator')
