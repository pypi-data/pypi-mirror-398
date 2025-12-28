from typing import Optional, List

from pydantic import BaseModel, Field


class TheStageBaseResponse(BaseModel):
    message: Optional[str] = Field(None, alias='message')
    is_success: Optional[bool] = Field(None, alias='isSuccess')


# TODO: add Generic then back doing that
class TheStageBasePaginatedResponse(TheStageBaseResponse):
    fields_with_error: List[str] = Field(None, alias='fieldsWithError')
