from pydantic import EmailStr, Field
from pydantic.main import BaseModel


class AuthPasswordResetRequestSchema(BaseModel):
    """
    Schema for password reset request.
    """

    email: EmailStr = Field(..., max_length=255)


class AuthPasswordResetSchema(BaseModel):
    """
    Schema for resetting a password using a password reset token.
    """

    token: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=128)
