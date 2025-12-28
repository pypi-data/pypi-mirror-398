from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    email: Optional[str] = Field(None, alias='email')



class UserProfileResponse(BaseModel):
    userProfile: Optional[UserProfile] = Field(None, alias='userProfile')
