# 📦 APIQ

**APIQ** is an elegant, fully asynchronous Python toolkit for building robust API clients with minimal code and maximal
type safety.
Define endpoints with simple decorators, leverage strict Pydantic models, and enjoy integrated rate limiting and
retries—**no inheritance required**.

[![PyPI](https://img.shields.io/pypi/v/apiq.svg?color=FFE873\&labelColor=3776AB)](https://pypi.python.org/pypi/apiq)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.12-black?color=FFE873\&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/apiq)](LICENSE)

![Downloads](https://pepy.tech/badge/apiq)
![Downloads](https://pepy.tech/badge/apiq/month)
![Downloads](https://pepy.tech/badge/apiq/week)

---

## Installation

```bash
pip install apiq
```

---

## Quickstart

### 1. Define your models

Use [Pydantic](https://docs.pydantic.dev/latest/) for type-safe request and response models:

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

---

### 2. Define your client class

Configure all core settings via the `@apiclient` decorator:

```python
from apiq import apiclient, endpoint


@apiclient(
    base_url="https://tonapi.io",
    headers={"Authorization": "Bearer <YOUR_API_KEY>"},
    version="v2",
    rps=1,
    retries=2,
)
class TONAPI:
    @endpoint("GET")
    async def status(self) -> dict:
        """Check API status (GET /status)"""

    @endpoint("GET")
    async def rates(self, tokens: str, currencies: str) -> dict:
        """Get token rates (GET /rates?tokens={tokens}&currencies={currencies})"""
```

**Note:**
No base class required. The decorator injects all async context, rate limiting, and HTTP logic automatically.

---

### 3. Group endpoints with namespaces (optional)

For logical endpoint grouping (e.g., `/accounts`, `/users`), use the `@apinamespace` decorator:

```python
from apiq import apinamespace, endpoint


@apinamespace("accounts")
class Accounts:

    @endpoint("GET", path="/{account_id}", as_model=AccountInfoResponse)
    async def info(self, account_id: str) -> AccountInfoResponse:
        """Retrieve account info (GET /accounts/{account_id})"""

    @endpoint("POST", path="/_bulk", as_model=BulkAccountsResponse)
    async def bulk_info(self, body: BulkAccountsRequest) -> BulkAccountsResponse:
        """Retrieve info for multiple accounts (POST /accounts/_bulk)"""

    @endpoint("POST", path="/_bulk")
    async def bulk_info_dict(self, body: dict) -> dict:
        """Retrieve info for multiple accounts (dict body) (POST /accounts/_bulk)"""
```

Then compose in your main client:

```python
@apiclient(
    base_url="https://tonapi.io",
    headers={"Authorization": "Bearer <YOUR_API_KEY>"},
    version="v2",
    rps=1,
    retries=2,
)
class TONAPI:
    # ... endpoints above ...

    @property
    def accounts(self) -> Accounts:
        return Accounts(self)
```

**Note:**

* You can use `"accounts"` or `"/accounts"` in `@apinamespace` — leading slash is optional and combined automatically
  with the endpoint path.

---

### 4. Usage

```python
async def main():
    tonapi = TONAPI()

    async with tonapi:
        # Direct endpoint
        status = await tonapi.status()
        print(status)
        # Namespaced endpoint
        account = await tonapi.accounts.info("UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0")
        print(account)
```

---

## API Configuration

All settings are passed to the `@apiclient` decorator:

| Name       | Type  | Description                                        | Default |
|------------|-------|----------------------------------------------------|---------|
| `base_url` | str   | Base URL for your API (must start with http/https) | —       |
| `headers`  | dict  | Default headers (e.g. Authorization)               | None    |
| `timeout`  | float | Default timeout (seconds)                          | None    |
| `rps`      | int   | Max requests per second (rate limit)               | 1       |
| `retries`  | int   | Max retries for 429 (Too Many Requests)            | 3       |
| `cookies`  | dict  | Cookies to send with every request                 | None    |

---

## Endpoints

* Use `@endpoint` to mark methods as API endpoints.
* All method arguments are automatically mapped to path or query parameters.
* For `POST` and `PUT` requests, the `body` can be a Pydantic model or a dict.
* The return type depends on `response_type` and the `as_model` argument.

---

### Notes

* All endpoints and clients are **fully async**; always use `async with` for resource cleanup.
* You may use flat client classes or split logic into namespaces as needed.
* If `as_model` is not set in `@endpoint`, the raw dict (parsed JSON) is returned.
* If `path` is omitted, the method name is used as the endpoint path (e.g., `status` → `/status`).

---

## Contribution

We welcome your contributions!
If you have ideas for improvement or find a bug, please create an issue or submit a pull request.

---

## License

Distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute in accordance with the license.
