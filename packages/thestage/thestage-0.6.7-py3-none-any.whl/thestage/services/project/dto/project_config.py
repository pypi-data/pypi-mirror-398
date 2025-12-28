from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class ProjectConfig(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    slug: str = Field(None, alias='slug')
    public_id: str = Field(None, alias='public_id')
    git_repository_url: str = Field(None, alias='git_repository_url')
    deploy_key_path: str = Field(None, alias='deploy_key_path')
    default_container_public_id: Optional[str] = Field(None, alias='default_container_public_id')
    prompt_for_default_container: bool = Field(True, alias='prompt_for_default_container')
