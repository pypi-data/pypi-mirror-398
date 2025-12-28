from typing import Optional

from pydantic import ConfigDict, BaseModel, Field


class FrontendStatusDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status_key: Optional[str] = Field(None, alias='statusKey')
    status_translation: Optional[str] = Field(None, alias='statusTranslation')
