
from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto


class InferenceSimulatorListResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulators: PaginatedEntityList[InferenceSimulatorDto] = Field(None, alias='inferenceSimulators')
