from typing import Optional

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.project.dto.inference_simulator_model_dto import InferenceSimulatorModelDto


class DeployInferenceModelToInstanceResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulatorPublicId: Optional[str] = Field(None, alias='inferenceSimulatorPublicId')


