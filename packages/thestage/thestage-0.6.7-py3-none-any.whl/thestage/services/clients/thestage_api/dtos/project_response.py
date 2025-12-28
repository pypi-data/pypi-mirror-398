from typing import Optional, List

from pydantic import Field, BaseModel, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class ProjectDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    slug: Optional[str] = Field(None, alias='slug')
    git_repository_url: Optional[str] = Field(None, alias='gitRepositoryUrl')
    git_repository_name: Optional[str] = Field(None, alias='gitRepositoryName')
    last_commit_hash: Optional[str] = Field(None, alias='lastCommitHash')
    last_commit_description: Optional[str] = Field(None, alias='lastCommitDescription')


class ProjectViewResponse(TheStageBaseResponse):
    project: Optional[ProjectDto] = Field(None, alias='project')
