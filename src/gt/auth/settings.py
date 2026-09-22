from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True, frozen=True, kw_only=True)
class AuthSettings:
    """
    Configuration settings for the authentication system.
    """

    ## cookie settings
    cookie_domain: str | None = None
    cookie_path: str = "/"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    session_expiration_minutes: int = 60 * 24 * 7  # 7 days

    ## email verification settings
    email_verification_token_expiry_minutes: int = 15  # 15 minutes
    email_verification_token_digit: int = 6

    ## password reset settings
    password_reset_token_expiry_minutes: int = 15  # 15 minutes
    password_reset_token_digit: int = 6

    ## oauth settings
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    oauth_app_url: str | None = None
