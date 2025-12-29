# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel
from .shared.api_error import APIError

__all__ = ["BulkIngestResponse", "Error"]


class Error(BaseModel):
    item_index: Optional[int] = None

    xproxy_result: Optional[APIError] = None


class BulkIngestResponse(BaseModel):
    ingest_count: int

    ingest_timestamp: datetime

    request_id: str

    error_count: Optional[int] = None

    errors: Optional[List[Error]] = None

    total_count: Optional[int] = None
