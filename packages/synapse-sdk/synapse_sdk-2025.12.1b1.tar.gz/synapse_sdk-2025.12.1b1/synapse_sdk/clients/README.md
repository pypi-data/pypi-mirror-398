# Synapse SDK Clients

HTTP client module providing both synchronous (sync) and asynchronous (async) API clients.

## Architecture Overview

```
synapse_sdk/clients/
├── __init__.py          # Public API exports
├── base.py              # BaseClient, AsyncBaseClient
├── protocols.py         # ClientProtocol, AsyncClientProtocol
├── utils.py             # Shared utility functions
├── validation.py        # ValidationMixin
├── exceptions.py        # Exception re-exports
├── _template.py         # New client template
├── agent/               # Agent API clients
│   ├── __init__.py      # AgentClient, AsyncAgentClient
│   ├── ray.py           # RayClientMixin
│   ├── async_ray.py     # AsyncRayClientMixin
│   ├── container.py     # ContainerClientMixin
│   └── plugin.py        # PluginClientMixin
└── backend/             # Backend API clients
    ├── __init__.py      # BackendClient
    ├── annotation.py    # AnnotationClientMixin
    ├── core.py          # CoreClientMixin
    ├── data_collection.py
    ├── hitl.py
    ├── integration.py
    ├── ml.py
    └── models.py        # Pydantic models
```

## Module Structure

### base.py

- `BaseClient`: Synchronous HTTP client based on requests
- `AsyncBaseClient`: Asynchronous HTTP client based on httpx
- Inherits `ValidationMixin` for Pydantic validation support

### protocols.py

- `ClientProtocol`: Synchronous client protocol
- `AsyncClientProtocol`: Asynchronous client protocol
- `@runtime_checkable` decorator enables runtime type checking

### utils.py

- `build_url()`: URL composition utility
- `extract_error_detail()`: Extract error details from response
- `parse_json_response()`: Parse JSON response

### validation.py

- `ValidationMixin`: Provides Pydantic validation methods
  - `_validate_response()`: Validate response data
  - `_validate_request()`: Validate request data

## Protocol-based Mixin Pattern

Use `ClientProtocol` as the `self` type hint in mixin classes:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol

class MyMixin:
    def get_something(self: ClientProtocol) -> dict:
        # IDE autocompletion supported
        return self._get('something/')
```

### Why Use Protocol?

1. **IDE Autocompletion**: Using `self: ClientProtocol` instead of `self: BaseClient` allows IDE to recognize methods like `_get`, `_post`, etc.
2. **Avoid Circular Imports**: Import only within `TYPE_CHECKING` block to prevent runtime circular dependencies
3. **Flexible Type Checking**: Supports structural typing without actual class inheritance

## Exception Hierarchy

```
ClientError (base)
├── ClientConnectionError  # Connection failure
├── ClientTimeoutError     # Timeout
├── HTTPError              # HTTP status code errors
│   ├── AuthenticationError (401)
│   ├── AuthorizationError (403)
│   ├── NotFoundError (404)
│   ├── ValidationError (400/422)
│   ├── RateLimitError (429)
│   └── ServerError (5xx)
└── StreamError            # Streaming errors
    ├── StreamLimitExceededError
    └── WebSocketError
```

### Exception Usage Example

```python
from synapse_sdk.exceptions import (
    ClientError,
    NotFoundError,
    AuthenticationError,
)

try:
    result = client.get_resource(123)
except NotFoundError:
    print("Resource not found")
except AuthenticationError:
    print("Authentication failed")
except ClientError as e:
    print(f"Client error: {e.status_code}")
```

## Guide for Adding New Clients

### 1. Copy Template

Create a new client by referencing `_template.py`:

```python
from synapse_sdk.clients.base import BaseClient

class MyApiClient(BaseClient):
    name = 'MyAPI'

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        return {'X-API-Key': self.api_key}

    def get_resource(self, resource_id: int) -> dict:
        return self._get(f'resources/{resource_id}/')
```

### 2. Use Mixin Pattern (Optional)

For large APIs, separate functionality into mixins:

```python
# my_api/users.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol

class UsersMixin:
    def list_users(self: ClientProtocol) -> list[dict]:
        return self._get('users/')

    def get_user(self: ClientProtocol, user_id: int) -> dict:
        return self._get(f'users/{user_id}/')

# my_api/__init__.py
from synapse_sdk.clients.base import BaseClient
from my_api.users import UsersMixin

class MyApiClient(UsersMixin, BaseClient):
    name = 'MyAPI'
    # ...
```

### 3. Pydantic Model Validation

Use Pydantic models for request/response validation:

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class MyApiClient(BaseClient):
    def create_user(self, data: dict) -> dict:
        return self._post(
            'users/',
            request_model=UserCreate,
            response_model=UserResponse,
            data=data,
        )
```

### 4. Async Client Implementation

```python
from synapse_sdk.clients.base import AsyncBaseClient

class AsyncMyApiClient(AsyncBaseClient):
    name = 'MyAPI'

    def __init__(self, base_url: str, api_key: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        return {'X-API-Key': self.api_key}

    async def get_resource(self, resource_id: int) -> dict:
        return await self._get(f'resources/{resource_id}/')

# Usage
async with AsyncMyApiClient(base_url, api_key) as client:
    result = await client.get_resource(123)
```

## Method Reference

### BaseClient / AsyncBaseClient

| Method                 | Description                  |
| ---------------------- | ---------------------------- |
| `_get(path, ...)`      | GET request                  |
| `_post(path, ...)`     | POST request                 |
| `_put(path, ...)`      | PUT request                  |
| `_patch(path, ...)`    | PATCH request                |
| `_delete(path, ...)`   | DELETE request               |
| `_list(path, ...)`     | List with pagination support |
| `_validate_response()` | Pydantic response validation |
| `_validate_request()`  | Pydantic request validation  |

### Utility Functions

| Function                                | Description                    |
| --------------------------------------- | ------------------------------ |
| `build_url(base, path, trailing_slash)` | URL composition                |
| `extract_error_detail(response)`        | Extract error details          |
| `parse_json_response(response)`         | Parse JSON response            |
| `raise_for_status(status_code, detail)` | Raise exception by status code |
