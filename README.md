# 📦 APIQ

[![PyPI](https://img.shields.io/pypi/v/apiq.svg?color=FFE873\&labelColor=3776AB)](https://pypi.python.org/pypi/apiq)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.12-black?color=FFE873\&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/apiq)](LICENSE)

**APIQ** is a modern Python toolkit for building both **synchronous** and **asynchronous** API clients with clean,
minimal code and full type safety.

Define endpoints using decorators like `@sync_endpoint` or `@async_endpoint`, structure logic with optional namespaces,
and leverage Pydantic models for strict request/response validation — all with built-in rate limiting and retries.

![Downloads](https://pepy.tech/badge/apiq)
![Downloads](https://pepy.tech/badge/apiq/month)
![Downloads](https://pepy.tech/badge/apiq/week)

## Installation

```bash
pip install apiq
```

## Quickstart

### 1. Define your models

Use [Pydantic](https://docs.pydantic.dev/latest/) to define request and response schemas with full type safety:

```python
from typing import List
from pydantic import BaseModel


class BulkAccountsRequest(BaseModel):
    account_ids: List[str]


class AccountInfoResponse(BaseModel):
    address: str
    balance: int
    status: str


class BulkAccountsResponse(BaseModel):
    accounts: List[AccountInfoResponse]
```

### 2. Define your client

Declare your API client by subclassing `AsyncClientAPI` and annotating endpoints with `@async_endpoint`:

```python
from apiq import AsyncClientAPI, async_endpoint


class AsyncTONAPI(AsyncClientAPI):
    base_url = "https://tonapi.io"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    version = "v2"
    rps = 1
    max_retries = 2

    @async_endpoint("GET")
    async def status(self) -> dict:
        """Check API status (GET /status)"""

    @async_endpoint("GET")
    async def rates(self, tokens: str, currencies: str) -> dict:
        """Get token rates (GET /rates?tokens={tokens}&currencies={currencies})"""
```

**Notes:**
* If you prefer synchronous clients, simply use `SyncClientAPI` with `@sync_endpoint` instead.
* For synchronous clients, use `SyncClientAPI` and `@sync_endpoint` — interface is fully symmetrical.
* Method arguments are automatically mapped to path and query parameters. The return value is parsed from JSON and
  returned as a `dict`, unless a `return_as=Model` is specified.

### 3. Group endpoints with namespaces (optional)

Use `AsyncAPINamespace` to logically organize endpoints under a common prefix (e.g., `/accounts`):

```python
from apiq import AsyncAPINamespace, async_endpoint


class Accounts(AsyncAPINamespace):
    namespace = "accounts"

    @async_endpoint("GET", path="/{account_id}", return_as=AccountInfoResponse)
    async def info(self, account_id: str) -> AccountInfoResponse:
        """Retrieve account information by account_id (GET /accounts/{account_id})"""

    @async_endpoint("POST", path="/_bulk", return_as=BulkAccountsResponse)
    async def bulk_info(self, payload: BulkAccountsRequest) -> BulkAccountsResponse:
        """Retrieve info for multiple accounts with a Pydantic model (POST /accounts/_bulk)"""

    @async_endpoint("POST", path="/_bulk")
    async def bulk_info_dict(self, payload: dict) -> dict:
        """Retrieve info for multiple accounts with a dict payload (POST /accounts/_bulk)"""
```

Then include the namespace in your main client:

```python
class AsyncTONAPI(AsyncClientAPI):
    base_url = "https://tonapi.io"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    version = "v2"
    rps = 1
    max_retries = 2

    # ... endpoints above ...

    @property
    def accounts(self) -> Accounts:
        return Accounts(self)
```

**Note:**
The `namespace` can be defined with or without a leading slash. It will be joined correctly with endpoint paths. Each
namespace instance receives the parent client instance automatically.

### 4. Usage

```python
async def main():
    tonapi = AsyncTONAPI()

    async with tonapi:
        # GET /status
        status = await tonapi.status()
        print(status)
```

**Note:**
Always use `async with` to open and close the session properly. All retries, throttling, and connection reuse are
handled under the hood.

## API Configuration

All settings are defined as class attributes on your client class:

| Name          | Type  | Description                                                       | Default |
|---------------|-------|-------------------------------------------------------------------|---------|
| `base_url`    | str   | Base URL of the API (must start with `http://` or `https://`)     | —       |
| `version`     | str   | Optional API version prefix (e.g. `"v1"` → `/v1/...` in requests) | None    |
| `rps`         | int   | Max requests per second (client-side rate limit)                  | 1       |
| `max_retries` | int   | Max automatic retries for HTTP 429 (Too Many Requests)            | 3       |
| `headers`     | dict  | Default headers to send with each request                         | None    |
| `cookies`     | dict  | Default cookies to send with each request                         | None    |
| `timeout`     | float | Default request timeout in seconds                                | None    |

**Note:**
The `version` field is automatically prefixed to all endpoint paths (e.g. `/v2/accounts/...`).
Rate limiting and retries are handled transparently and apply only per-client instance.

## Endpoints

* Use `@async_endpoint(method, path=..., return_as=...)` to declare each endpoint.
* All method arguments are automatically mapped:

    * Scalars → query/path parameters
    * dict or Pydantic models → request body
* `return_as=Model` lets you parse responses into Pydantic models.
* If omitted, response is returned as `dict`.

**Note:**
If `path` is omitted, the method name becomes the endpoint path (e.g. `rates` → `/rates`). You can define both flat and
namespaced methods together.

## Notes

* Fully asynchronous: all clients and endpoints require `async with`.
* Zero boilerplate: request building, error handling, retries, and throttling are automatic.
* Namespaces help organize large APIs, but are optional.
* Both dicts and Pydantic models are supported in request payloads.
* Great for building typed SDKs or internal tools.

## Contribution

We welcome your contributions!
If you find a bug or have an idea, please open an issue or submit a pull request.

## License

Distributed under the [MIT License](LICENSE).
Use freely for commercial or personal projects.