# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["IngestUnits"]


class IngestUnits(BaseModel):
    input: Optional[int] = None

    output: Optional[int] = None
