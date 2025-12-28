from typing import Optional, List

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.enums.container_pending_action import DockerContainerAction

class DockerContainerActionRequestDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    container_public_id: Optional[str] = Field(None, alias='dockerContainerPublicId')
    action: DockerContainerAction = Field(None, alias='action')
