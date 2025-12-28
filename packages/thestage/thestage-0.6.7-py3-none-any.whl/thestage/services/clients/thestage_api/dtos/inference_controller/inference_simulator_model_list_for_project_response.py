
from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto
from thestage.services.project.dto.inference_simulator_model_dto import InferenceSimulatorModelDto


class InferenceSimulatorModelListForProjectResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulatorModels: PaginatedEntityList[InferenceSimulatorModelDto] = Field(None, alias='inferenceSimulatorModels')
