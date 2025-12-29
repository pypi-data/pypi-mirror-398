# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CategoryResourceResponse", "Units", "AwsBedrockResource", "AzureResource", "GoogleVertexResource"]


class Units(BaseModel):
    input_price: Optional[float] = None

    output_price: Optional[float] = None


class AwsBedrockResource(BaseModel):
    aws_model_units: int = FieldInfo(alias="model_units")


class AzureResource(BaseModel):
    ptus: int


class GoogleVertexResource(BaseModel):
    gsus: int


class CategoryResourceResponse(BaseModel):
    active: bool

    category: str

    proxy_allowed: bool

    resource: str

    resource_id: str

    start_timestamp: datetime

    units: Dict[str, Units]

    aliased_resource: Optional[str] = None

    aws_bedrock_resource: Optional[AwsBedrockResource] = None

    azure_resource: Optional[AzureResource] = None

    character_billing: Optional[bool] = None

    cost_per_hour: Optional[float] = None

    deprecated_timestamp: Optional[datetime] = None

    description: Optional[str] = None

    end_timestamp: Optional[datetime] = None

    google_vertex_resource: Optional[GoogleVertexResource] = None

    large_context_threshold: Optional[int] = None

    max_input_units: Optional[int] = None

    max_output_units: Optional[int] = None

    max_total_units: Optional[int] = None

    reservation_id: Optional[str] = None
