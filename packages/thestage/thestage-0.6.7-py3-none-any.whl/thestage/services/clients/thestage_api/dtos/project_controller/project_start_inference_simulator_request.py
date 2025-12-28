from typing import Optional

from pydantic import Field, ConfigDict, BaseModel


class ProjectStartInferenceSimulatorRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    projectPublicId: str = Field(None, alias='projectPublicId')
    instanceRentedPublicId: Optional[str] = Field(None, alias='instanceRentedPublicId')
    instanceRentedSlug: Optional[str] = Field(None, alias='instanceRentedSlug')
    selfhostedInstancePublicId: Optional[str] = Field(None, alias='selfhostedInstancePublicId')
    selfhostedInstanceSlug: Optional[str] = Field(None, alias='selfhostedInstanceSlug')
    commitHash: Optional[str] = Field(None, alias='commitHash')
    inferenceDir: Optional[str] = Field(None, alias='inferenceDir')
    isSkipInstallation: Optional[bool] = Field(False, alias='isSkipInstallation')