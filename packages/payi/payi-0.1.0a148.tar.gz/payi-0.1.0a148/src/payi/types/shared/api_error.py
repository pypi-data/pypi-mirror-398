# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from .xproxy_error import XproxyError

__all__ = ["APIError"]


class APIError(BaseModel):
    message: str

    status_code: int = FieldInfo(alias="statusCode")

    xproxy_error: Optional[XproxyError] = None
