from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DockerContainerEntity(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    public_id: Optional[str] = Field(None, alias='ID')
    slug: Optional[str] = Field(None, alias='NAME')
    status: Optional[str] = Field(None, alias='STATUS')
    project_slug: Optional[str] = Field(None, alias='PROJECT NAME')
    instance_type: Optional[str] = Field(None, alias='INSTANCE TYPE')
    instance_slug: Optional[str] = Field(None, alias='INSTANCE NAME')
    docker_image: Optional[str] = Field(None, alias='DOCKER IMAGE')
