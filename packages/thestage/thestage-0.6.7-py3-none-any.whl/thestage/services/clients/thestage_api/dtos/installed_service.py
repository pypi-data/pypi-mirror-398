from typing import Optional, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class DockerContainerInstalledServiceDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, alias='name')
    port: Optional[int] = Field(None, alias='port')
    url: Optional[str] = Field(None, alias='url')
    variables: Dict[str, str] = Field(default_factory=dict, alias='variables')


class DockerContainerInstalledServicesDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    installed_services: List[DockerContainerInstalledServiceDto] = Field(default_factory=list, alias='installedServices')