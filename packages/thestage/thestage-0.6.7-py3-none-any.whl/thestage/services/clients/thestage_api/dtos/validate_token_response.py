from typing import Optional, List, Dict

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse, TheStageBasePaginatedResponse


class ValidateTokenResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    allowedCliCommands: Optional[Dict[str, bool]] = Field(default={}, alias='allowedCliCommands')
