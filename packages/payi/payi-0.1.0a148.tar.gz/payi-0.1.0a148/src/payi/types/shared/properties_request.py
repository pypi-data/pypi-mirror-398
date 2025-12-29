# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ..._models import BaseModel

__all__ = ["PropertiesRequest"]


class PropertiesRequest(BaseModel):
    properties: Dict[str, Optional[str]]
