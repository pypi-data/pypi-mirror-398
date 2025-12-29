# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel
from .shared.xproxy_result import XproxyResult

__all__ = ["RequestResult"]


class RequestResult(BaseModel):
    xproxy_result: XproxyResult
