from pydantic import Field
from pydantic.main import BaseModel


class AuthProfileUpdateSchema(BaseModel):
    """
    Schema for updating a user's profile.
    """

    full_name: str | None = Field(None, max_length=255)
    avatar_bg: str | None = Field(None, max_length=255)
    avatar: str | None = Field(None, max_length=255)


class AuthDeactivateSchema(BaseModel):
    """
    Schema for deactivating a user account.
    """

    password: str = Field(..., max_length=128)
