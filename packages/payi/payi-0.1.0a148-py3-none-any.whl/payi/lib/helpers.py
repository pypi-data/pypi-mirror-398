from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Union

__all__ = ['_set_attr_safe'] 

PAYI_BASE_URL = "https://api.pay-i.com"

class PayiHeaderNames:
    limit_ids:str  = "xProxy-Limit-IDs"
    request_tags:str = "xProxy-Request-Tags"
    request_properties:str = "xProxy-Request-Properties"
    use_case_id:str = "xProxy-UseCase-ID"
    use_case_name:str = "xProxy-UseCase-Name"
    use_case_version:str = "xProxy-UseCase-Version"
    use_case_step:str = "xProxy-UseCase-Step"
    use_case_properties:str = "xProxy-UseCase-Properties"
    user_id:str = "xProxy-User-ID"
    account_name:str = "xProxy-Account-Name"
    price_as_category:str = "xProxy-PriceAs-Category"
    price_as_resource:str = "xProxy-PriceAs-Resource"
    provider_base_uri = "xProxy-Provider-BaseUri"
    resource_scope:str = "xProxy-Resource-Scope"
    api_key:str = "xProxy-Api-Key"
    logging_disable:str = "xProxy-Logging-Disable"
    
class PayiCategories:
    anthropic:str  = "system.anthropic"
    openai:str = "system.openai"
    azure_openai:str = "system.azureopenai"
    azure:str = "system.azure"
    aws_bedrock:str = "system.aws.bedrock"
    google_vertex:str = "system.google.vertex"

class PayiPropertyNames:
    failure:str = "system.failure"
    failure_description:str = "system.failure.description"

    account_name:str = "system.account_name"
    use_case_step:str = "system.use_case_step"
    user_id:str = "system.user_id"

    aws_bedrock_guardrail_id:str = "system.aws.bedrock.guardrail.id"
    aws_bedrock_guardrail_version:str = "system.aws.bedrock.guardrail.version"
    aws_bedrock_guardrail_action:str = "system.aws.bedrock.guardrail.action"

class PayiResourceScopes:
    global_scope: str = "global"
    datazone_scope: str = "datazone"
    region_scope: str = "region"

def create_limit_header_from_ids(*, limit_ids: List[str]) -> Dict[str, str]:
    if not isinstance(limit_ids, list):  # type: ignore
        raise TypeError("limit_ids must be a list")

    valid_ids = [id.strip() for id in limit_ids if isinstance(id, str) and id.strip()]  # type: ignore

    return { PayiHeaderNames.limit_ids: ",".join(valid_ids) } if valid_ids else {}

def create_request_header_from_tags(*, request_tags: List[str]) -> Dict[str, str]:
    if not isinstance(request_tags, list):  # type: ignore
        raise TypeError("request_tags must be a list")

    valid_tags = [tag.strip() for tag in request_tags if isinstance(tag, str) and tag.strip()]  # type: ignore

    return { PayiHeaderNames.request_tags: ",".join(valid_tags) } if valid_tags else {}

def _compact_json(data: Any) -> str:
    return json.dumps(data, separators=(',', ':'))  

def create_headers(
    *,
    limit_ids: Union[List[str], None] = None,
    request_tags: Union[List[str], None] = None,
    user_id: Union[str, None] = None,
    account_name: Union[str, None] = None,
    use_case_id: Union[str, None] = None,
    use_case_name: Union[str, None] = None,
    use_case_version: Union[int, None] = None,
    use_case_step: Union[str, None] = None,
    use_case_properties: Union[Dict[str, str], None] = None,
    request_properties: Union[Dict[str, str], None] = None,
    price_as_category: Union[str, None] = None,
    price_as_resource: Union[str, None] = None,
    resource_scope: Union[str, None] = None,
    log_prompt_and_response: Union[bool, None] = None,
) -> Dict[str, str]:
    headers: Dict[str, str] = {}

    if limit_ids:
        headers.update(create_limit_header_from_ids(limit_ids=limit_ids))
    if request_tags:
        headers.update(create_request_header_from_tags(request_tags=request_tags))
    if user_id:
        headers.update({ PayiHeaderNames.user_id: user_id})
    if account_name:
        headers.update({ PayiHeaderNames.account_name: account_name})
    if use_case_id:
        headers.update({ PayiHeaderNames.use_case_id: use_case_id})
    if use_case_name:
        headers.update({ PayiHeaderNames.use_case_name: use_case_name})
    if use_case_version:
        headers.update({ PayiHeaderNames.use_case_version: str(use_case_version)})
    if use_case_properties:
        headers.update({ PayiHeaderNames.use_case_properties: _compact_json(use_case_properties) })
    if request_properties:
        headers.update({ PayiHeaderNames.request_properties: _compact_json(request_properties) })
    if use_case_step:
        headers.update({ PayiHeaderNames.use_case_step: use_case_step})
    if price_as_category:
        headers.update({ PayiHeaderNames.price_as_category: price_as_category})
    if price_as_resource:
        headers.update({ PayiHeaderNames.price_as_resource: price_as_resource})
    if resource_scope:
        headers.update({ PayiHeaderNames.resource_scope: resource_scope })
    if log_prompt_and_response is not None and log_prompt_and_response is False:
        headers.update({ PayiHeaderNames.logging_disable: "True" })
    return headers

def _resolve_payi_base_url(payi_base_url: Union[str, None]) -> str:
    if payi_base_url:
        return payi_base_url

    payi_base_url = os.environ.get("PAYI_BASE_URL", None)

    if payi_base_url:
        return payi_base_url

    return PAYI_BASE_URL

def payi_anthropic_url(payi_base_url: Union[str, None] = None) -> str:
    return _resolve_payi_base_url(payi_base_url=payi_base_url) + "/api/v1/proxy/anthropic"

def payi_openai_url(payi_base_url: Union[str, None] = None) -> str:
    return _resolve_payi_base_url(payi_base_url=payi_base_url) +  "/api/v1/proxy/openai/v1"

def payi_azure_openai_url(payi_base_url: Union[str, None] = None) -> str:
    return _resolve_payi_base_url(payi_base_url=payi_base_url) + "/api/v1/proxy/azure.openai"

def payi_azure_anthropic_url(payi_base_url: Union[str, None] = None) -> str:
    return _resolve_payi_base_url(payi_base_url=payi_base_url) + "/api/v1/proxy/azure.anthropic"

def payi_aws_bedrock_url(payi_base_url: Union[str, None] = None) -> str:
    return _resolve_payi_base_url(payi_base_url=payi_base_url) + "/api/v1/proxy/aws.bedrock"

# def payi_google_vertex_url(payi_base_url: Union[str, None] = None) -> str:
#     return _resolve_payi_base_url(payi_base_url=payi_base_url) + "/api/v1/proxy/google.vertex"

def _set_attr_safe(o: Any, attr_name: str, attr_value: Any) -> None:
    try:
        if hasattr(o, '__pydantic_private__') and o.__pydantic_private__ is not None:
            o.__pydantic_private__[attr_name] = attr_value

        if hasattr(o, '__dict__'):
            # Use object.__setattr__ to bypass Pydantic validation
            # This allows setting attributes outside the model schema without triggering forbid=true errors
            object.__setattr__(o, attr_name, attr_value)
        elif isinstance(o, dict):
            o[attr_name] = attr_value
        else:
            setattr(o, attr_name, attr_value)

    except Exception:
        # _g_logger.debug(f"Could not set attribute {attr_name}: {e}")
        pass

