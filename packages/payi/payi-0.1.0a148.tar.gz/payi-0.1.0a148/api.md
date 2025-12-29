# Shared Types

```python
from payi.types import (
    APIError,
    IngestUnits,
    PayICommonModelsBudgetManagementCostDetailsBase,
    PayICommonModelsBudgetManagementCreateLimitBase,
    PropertiesRequest,
    PropertiesResponse,
    XproxyError,
    XproxyResult,
)
```

# Limits

Types:

```python
from payi.types import (
    CostData,
    CostDetails,
    DefaultResponse,
    LimitHistoryResponse,
    LimitResponse,
    RequestsData,
    TotalCostData,
    LimitListResponse,
)
```

Methods:

- <code title="post /api/v1/limits">client.limits.<a href="./src/payi/resources/limits/limits.py">create</a>(\*\*<a href="src/payi/types/limit_create_params.py">params</a>) -> <a href="./src/payi/types/limit_response.py">LimitResponse</a></code>
- <code title="get /api/v1/limits/{limit_id}">client.limits.<a href="./src/payi/resources/limits/limits.py">retrieve</a>(limit_id) -> <a href="./src/payi/types/limit_response.py">LimitResponse</a></code>
- <code title="put /api/v1/limits/{limit_id}">client.limits.<a href="./src/payi/resources/limits/limits.py">update</a>(limit_id, \*\*<a href="src/payi/types/limit_update_params.py">params</a>) -> <a href="./src/payi/types/limit_response.py">LimitResponse</a></code>
- <code title="get /api/v1/limits">client.limits.<a href="./src/payi/resources/limits/limits.py">list</a>(\*\*<a href="src/payi/types/limit_list_params.py">params</a>) -> <a href="./src/payi/types/limit_list_response.py">SyncCursorPage[LimitListResponse]</a></code>
- <code title="delete /api/v1/limits/{limit_id}">client.limits.<a href="./src/payi/resources/limits/limits.py">delete</a>(limit_id) -> <a href="./src/payi/types/default_response.py">DefaultResponse</a></code>
- <code title="post /api/v1/limits/{limit_id}/reset">client.limits.<a href="./src/payi/resources/limits/limits.py">reset</a>(limit_id, \*\*<a href="src/payi/types/limit_reset_params.py">params</a>) -> <a href="./src/payi/types/limit_history_response.py">LimitHistoryResponse</a></code>

## Properties

Types:

```python
from payi.types.limits import PropertyUpdateResponse
```

Methods:

- <code title="put /api/v1/limits/{limit_id}/properties">client.limits.properties.<a href="./src/payi/resources/limits/properties.py">update</a>(limit_id, \*\*<a href="src/payi/types/limits/property_update_params.py">params</a>) -> <a href="./src/payi/types/limits/property_update_response.py">PropertyUpdateResponse</a></code>

# Ingest

Types:

```python
from payi.types import (
    BulkIngestRequest,
    BulkIngestResponse,
    IngestRequest,
    IngestResponse,
    PayICommonModelsAPIRouterHeaderInfo,
)
```

Methods:

- <code title="post /api/v1/ingest/bulk">client.ingest.<a href="./src/payi/resources/ingest.py">bulk</a>(\*\*<a href="src/payi/types/ingest_bulk_params.py">params</a>) -> <a href="./src/payi/types/bulk_ingest_response.py">BulkIngestResponse</a></code>
- <code title="post /api/v1/ingest">client.ingest.<a href="./src/payi/resources/ingest.py">units</a>(\*\*<a href="src/payi/types/ingest_units_params.py">params</a>) -> <a href="./src/payi/types/ingest_response.py">IngestResponse</a></code>

# Categories

Types:

```python
from payi.types import (
    CategoryResourceResponse,
    CategoryResponse,
    CategoryDeleteResponse,
    CategoryDeleteResourceResponse,
)
```

Methods:

- <code title="get /api/v1/categories">client.categories.<a href="./src/payi/resources/categories/categories.py">list</a>(\*\*<a href="src/payi/types/category_list_params.py">params</a>) -> <a href="./src/payi/types/category_response.py">SyncCursorPage[CategoryResponse]</a></code>
- <code title="delete /api/v1/categories/{category}">client.categories.<a href="./src/payi/resources/categories/categories.py">delete</a>(category) -> <a href="./src/payi/types/category_delete_response.py">CategoryDeleteResponse</a></code>
- <code title="delete /api/v1/categories/{category}/resources/{resource}">client.categories.<a href="./src/payi/resources/categories/categories.py">delete_resource</a>(resource, \*, category) -> <a href="./src/payi/types/category_delete_resource_response.py">CategoryDeleteResourceResponse</a></code>
- <code title="get /api/v1/categories/{category}/resources">client.categories.<a href="./src/payi/resources/categories/categories.py">list_resources</a>(category, \*\*<a href="src/payi/types/category_list_resources_params.py">params</a>) -> <a href="./src/payi/types/category_resource_response.py">SyncCursorPage[CategoryResourceResponse]</a></code>

## Resources

Methods:

- <code title="post /api/v1/categories/{category}/resources/{resource}">client.categories.resources.<a href="./src/payi/resources/categories/resources.py">create</a>(resource, \*, category, \*\*<a href="src/payi/types/categories/resource_create_params.py">params</a>) -> <a href="./src/payi/types/category_resource_response.py">CategoryResourceResponse</a></code>
- <code title="get /api/v1/categories/{category}/resources/{resource}/{resource_id}">client.categories.resources.<a href="./src/payi/resources/categories/resources.py">retrieve</a>(resource_id, \*, category, resource) -> <a href="./src/payi/types/category_resource_response.py">CategoryResourceResponse</a></code>
- <code title="get /api/v1/categories/{category}/resources/{resource}">client.categories.resources.<a href="./src/payi/resources/categories/resources.py">list</a>(resource, \*, category, \*\*<a href="src/payi/types/categories/resource_list_params.py">params</a>) -> <a href="./src/payi/types/category_resource_response.py">SyncCursorPage[CategoryResourceResponse]</a></code>
- <code title="delete /api/v1/categories/{category}/resources/{resource}/{resource_id}">client.categories.resources.<a href="./src/payi/resources/categories/resources.py">delete</a>(resource_id, \*, category, resource) -> <a href="./src/payi/types/category_resource_response.py">CategoryResourceResponse</a></code>

# UseCases

Types:

```python
from payi.types import UseCaseInstanceResponse
```

Methods:

- <code title="post /api/v1/use_cases/instances/{use_case_name}">client.use_cases.<a href="./src/payi/resources/use_cases/use_cases.py">create</a>(use_case_name) -> <a href="./src/payi/types/use_case_instance_response.py">UseCaseInstanceResponse</a></code>
- <code title="get /api/v1/use_cases/instances/{use_case_name}/{use_case_id}">client.use_cases.<a href="./src/payi/resources/use_cases/use_cases.py">retrieve</a>(use_case_id, \*, use_case_name) -> <a href="./src/payi/types/use_case_instance_response.py">UseCaseInstanceResponse</a></code>
- <code title="delete /api/v1/use_cases/instances/{use_case_name}/{use_case_id}">client.use_cases.<a href="./src/payi/resources/use_cases/use_cases.py">delete</a>(use_case_id, \*, use_case_name) -> <a href="./src/payi/types/use_case_instance_response.py">UseCaseInstanceResponse</a></code>

## Kpis

Types:

```python
from payi.types.use_cases import KpiListResponse
```

Methods:

- <code title="put /api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis/{kpi_name}">client.use_cases.kpis.<a href="./src/payi/resources/use_cases/kpis.py">update</a>(kpi_name, \*, use_case_name, use_case_id, \*\*<a href="src/payi/types/use_cases/kpi_update_params.py">params</a>) -> None</code>
- <code title="get /api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis">client.use_cases.kpis.<a href="./src/payi/resources/use_cases/kpis.py">list</a>(use_case_id, \*, use_case_name, \*\*<a href="src/payi/types/use_cases/kpi_list_params.py">params</a>) -> <a href="./src/payi/types/use_cases/kpi_list_response.py">SyncCursorPage[KpiListResponse]</a></code>

## Definitions

Types:

```python
from payi.types.use_cases import UseCaseDefinitionResponse
```

Methods:

- <code title="post /api/v1/use_cases/definitions">client.use_cases.definitions.<a href="./src/payi/resources/use_cases/definitions/definitions.py">create</a>(\*\*<a href="src/payi/types/use_cases/definition_create_params.py">params</a>) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>
- <code title="get /api/v1/use_cases/definitions/{use_case_name}">client.use_cases.definitions.<a href="./src/payi/resources/use_cases/definitions/definitions.py">retrieve</a>(use_case_name) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>
- <code title="put /api/v1/use_cases/definitions/{use_case_name}">client.use_cases.definitions.<a href="./src/payi/resources/use_cases/definitions/definitions.py">update</a>(use_case_name, \*\*<a href="src/payi/types/use_cases/definition_update_params.py">params</a>) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>
- <code title="get /api/v1/use_cases/definitions">client.use_cases.definitions.<a href="./src/payi/resources/use_cases/definitions/definitions.py">list</a>(\*\*<a href="src/payi/types/use_cases/definition_list_params.py">params</a>) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">SyncCursorPage[UseCaseDefinitionResponse]</a></code>
- <code title="delete /api/v1/use_cases/definitions/{use_case_name}">client.use_cases.definitions.<a href="./src/payi/resources/use_cases/definitions/definitions.py">delete</a>(use_case_name) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>

### Kpis

Types:

```python
from payi.types.use_cases.definitions import (
    KpiCreateResponse,
    KpiRetrieveResponse,
    KpiUpdateResponse,
    KpiListResponse,
    KpiDeleteResponse,
)
```

Methods:

- <code title="post /api/v1/use_cases/definitions/{use_case_name}/kpis">client.use_cases.definitions.kpis.<a href="./src/payi/resources/use_cases/definitions/kpis.py">create</a>(use_case_name, \*\*<a href="src/payi/types/use_cases/definitions/kpi_create_params.py">params</a>) -> <a href="./src/payi/types/use_cases/definitions/kpi_create_response.py">KpiCreateResponse</a></code>
- <code title="get /api/v1/use_cases/definitions/{use_case_name}/kpis/{kpi_name}">client.use_cases.definitions.kpis.<a href="./src/payi/resources/use_cases/definitions/kpis.py">retrieve</a>(kpi_name, \*, use_case_name) -> <a href="./src/payi/types/use_cases/definitions/kpi_retrieve_response.py">KpiRetrieveResponse</a></code>
- <code title="put /api/v1/use_cases/definitions/{use_case_name}/kpis/{kpi_name}">client.use_cases.definitions.kpis.<a href="./src/payi/resources/use_cases/definitions/kpis.py">update</a>(kpi_name, \*, use_case_name, \*\*<a href="src/payi/types/use_cases/definitions/kpi_update_params.py">params</a>) -> <a href="./src/payi/types/use_cases/definitions/kpi_update_response.py">KpiUpdateResponse</a></code>
- <code title="get /api/v1/use_cases/definitions/{use_case_name}/kpis">client.use_cases.definitions.kpis.<a href="./src/payi/resources/use_cases/definitions/kpis.py">list</a>(use_case_name, \*\*<a href="src/payi/types/use_cases/definitions/kpi_list_params.py">params</a>) -> <a href="./src/payi/types/use_cases/definitions/kpi_list_response.py">SyncCursorPage[KpiListResponse]</a></code>
- <code title="delete /api/v1/use_cases/definitions/{use_case_name}/kpis/{kpi_name}">client.use_cases.definitions.kpis.<a href="./src/payi/resources/use_cases/definitions/kpis.py">delete</a>(kpi_name, \*, use_case_name) -> <a href="./src/payi/types/use_cases/definitions/kpi_delete_response.py">KpiDeleteResponse</a></code>

### LimitConfig

Methods:

- <code title="post /api/v1/use_cases/definitions/{use_case_name}/limit_config">client.use_cases.definitions.limit_config.<a href="./src/payi/resources/use_cases/definitions/limit_config.py">create</a>(use_case_name, \*\*<a href="src/payi/types/use_cases/definitions/limit_config_create_params.py">params</a>) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>
- <code title="delete /api/v1/use_cases/definitions/{use_case_name}/limit_config">client.use_cases.definitions.limit_config.<a href="./src/payi/resources/use_cases/definitions/limit_config.py">delete</a>(use_case_name) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>

### Version

Methods:

- <code title="post /api/v1/use_cases/definitions/{use_case_name}/increment_version">client.use_cases.definitions.version.<a href="./src/payi/resources/use_cases/definitions/version.py">increment</a>(use_case_name) -> <a href="./src/payi/types/use_cases/use_case_definition_response.py">UseCaseDefinitionResponse</a></code>

## Properties

Methods:

- <code title="put /api/v1/use_cases/instances/{use_case_name}/{use_case_id}/properties">client.use_cases.properties.<a href="./src/payi/resources/use_cases/properties.py">update</a>(use_case_id, \*, use_case_name, \*\*<a href="src/payi/types/use_cases/property_update_params.py">params</a>) -> <a href="./src/payi/types/use_case_instance_response.py">UseCaseInstanceResponse</a></code>

# Requests

Types:

```python
from payi.types import RequestResult
```

## RequestID

### Result

Methods:

- <code title="get /api/v1/requests/{request_id}/result">client.requests.request_id.result.<a href="./src/payi/resources/requests/request_id/result.py">retrieve</a>(request_id) -> <a href="./src/payi/types/request_result.py">RequestResult</a></code>

### Properties

Methods:

- <code title="put /api/v1/requests/{request_id}/properties">client.requests.request_id.properties.<a href="./src/payi/resources/requests/request_id/properties.py">update</a>(request_id, \*\*<a href="src/payi/types/requests/request_id/property_update_params.py">params</a>) -> <a href="./src/payi/types/shared/properties_response.py">PropertiesResponse</a></code>

## ResponseID

### Result

Methods:

- <code title="get /api/v1/requests/provider/{category}/{provider_response_id}/result">client.requests.response_id.result.<a href="./src/payi/resources/requests/response_id/result.py">retrieve</a>(provider_response_id, \*, category) -> <a href="./src/payi/types/request_result.py">RequestResult</a></code>

### Properties

Methods:

- <code title="put /api/v1/requests/provider/{category}/{provider_response_id}/properties">client.requests.response_id.properties.<a href="./src/payi/resources/requests/response_id/properties.py">update</a>(provider_response_id, \*, category, \*\*<a href="src/payi/types/requests/response_id/property_update_params.py">params</a>) -> <a href="./src/payi/types/shared/properties_response.py">PropertiesResponse</a></code>
