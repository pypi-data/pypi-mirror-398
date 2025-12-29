# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["RequestsData"]


class RequestsData(BaseModel):
    blocked: int

    blocked_external: int

    exceeded: int

    failed: int

    ok: int

    overrun: int

    total: int
