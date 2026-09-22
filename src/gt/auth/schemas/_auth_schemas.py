import random

from pydantic import EmailStr, Field, model_validator
from pydantic.main import BaseModel

PASTEL_COLORS = [
    "#F87171",  # red
    "#FB923C",  # orange
    "#FACC15",  # yellow
    "#4ADE80",  # green
    "#60A5FA",  # blue
    "#818CF8",  # indigo
    "#C084FC",  # purple
    "#F472B6",  # pink
    "#2DD4BF",  # teal
]


def random_avatar_color() -> str:
    """
    Returns a random pastel color from the predefined list of pastel colors.
    """
    return random.choice(PASTEL_COLORS)


class AuthUserRegisterSchema(BaseModel):
    """
    Schema for user registration.
    """

    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None
    avatar_bg: str | None = Field(default_factory=random_avatar_color)

    @model_validator(mode="after")
    def calculate_full_name(self):
        """
        Calculate the full name from the email if not provided.
        """
        if not self.full_name:
            username = self.email.split("@", 1)[0]
            self.full_name = (
                username.replace(".", " ").replace("_", " ").replace("-", " ").title()
            )
        return self


class AuthLoginRequestSchema(BaseModel):
    """
    Schema for user login request.
    """

    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., max_length=128)
