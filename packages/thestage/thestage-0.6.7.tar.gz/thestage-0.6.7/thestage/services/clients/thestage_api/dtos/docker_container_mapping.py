from typing import Optional, List, Dict

from pydantic import Field, BaseModel, ConfigDict


class DockerContainerMappingDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    directory_mappings: Dict[str, str] = Field(default_factory=dict, alias='directoryMappings')
    port_mappings: Dict[str, str] = Field(default_factory=dict, alias='portMappings')
