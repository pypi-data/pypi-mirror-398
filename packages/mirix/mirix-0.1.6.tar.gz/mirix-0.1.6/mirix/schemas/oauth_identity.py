from datetime import datetime
from typing import Optional

from pydantic import Field

from mirix.schemas.mirix_base import MirixBase


class OAuthIdentity(MirixBase):
    """OAuth identity linked to a dashboard client."""

    id: str = Field(..., description="The unique identifier of the OAuth identity.")
    provider: str = Field(..., description="OAuth provider name (e.g., google).")
    provider_subject: str = Field(..., description="Provider user ID (subject).")
    email: Optional[str] = Field(None, description="Email from the provider, if available.")
    client_id: str = Field(..., description="Associated client ID.")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp.")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp.")
    is_deleted: bool = Field(False, description="Whether this identity is deleted.")
