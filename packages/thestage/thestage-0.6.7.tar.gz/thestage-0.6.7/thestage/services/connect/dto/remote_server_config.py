from typing import Optional, Dict

from pydantic import Field, ConfigDict, BaseModel


class RemoteServerConfig(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ip_address_to_ssh_key_map: Dict[str, str] = Field(None, alias='ip_address_to_ssh_key_map')
