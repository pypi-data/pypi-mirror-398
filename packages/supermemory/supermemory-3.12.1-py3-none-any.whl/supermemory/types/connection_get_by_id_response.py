# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ConnectionGetByIDResponse"]


class ConnectionGetByIDResponse(BaseModel):
    id: str

    created_at: str = FieldInfo(alias="createdAt")

    provider: str

    document_limit: Optional[float] = FieldInfo(alias="documentLimit", default=None)

    email: Optional[str] = None

    expires_at: Optional[str] = FieldInfo(alias="expiresAt", default=None)

    metadata: Optional[Dict[str, object]] = None
