# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from .._models import BaseModel
from .shared.xproxy_result import XproxyResult

__all__ = ["IngestResponse"]


class IngestResponse(BaseModel):
    event_timestamp: datetime

    ingest_timestamp: datetime

    request_id: str

    xproxy_result: XproxyResult
