# 📦 APIQ

**APIQ** is an elegant, fast, fully asynchronous Python framework for building API clients with minimal boilerplate. It
provides structured endpoints via intuitive decorators, strict Pydantic models, and integrated rate limiting.

[![PyPI](https://img.shields.io/pypi/v/apiq.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/apiq)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.12-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/apiq)](LICENSE)

![Downloads](https://pepy.tech/badge/apiq)
![Downloads](https://pepy.tech/badge/apiq/month)
![Downloads](https://pepy.tech/badge/apiq/week)

## Installation

```bash
pip install apiq
```

## Usage

### Creating your API client

To create your API client, **extend `APIClient`** and define:

* `url`: Base URL of your API (**required**).
* `version`: API version path segment (**required**, use `""` if absent).

```python
import logging
from typing import List

from pydantic import BaseModel
from apiq import APINamespace, endpoint, APIClient


class TONAPI(APIClient):
    url = "https://tonapi.io"
    version = "v2"
```

### Initialization parameters

When instantiating your client, you can configure:

| Name          | Type | Description                                                                               | Default |
|---------------|------|-------------------------------------------------------------------------------------------|---------|
| `headers`     | dict | Default headers, e.g. Authorization tokens or Content-Type.                               | `{}`    |
| `timeout`     | int  | Request timeout in seconds.                                                               | `10`    |
| `rps`         | int  | Maximum requests per second (rate limiting). Controls throughput and prevents 429 errors. | `1`     |
| `max_retries` | int  | Number of retries on 429 responses.                                                       | `3`     |
| `debug`       | bool | Enable logging of requests and responses.                                                 | `False` |

```python
tonapi = TONAPI(
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    timeout=15,
    rps=5,
    max_retries=2,
    debug=True
)
```

### Defining models

Use Pydantic models to define your request and response schemas.

* POST request bodies can be provided as either Pydantic models or plain dicts, depending on your endpoint declaration.
* If no response model is specified, the raw response will be returned as a dict.

```python
class BulkAccountsRequest(BaseModel):
    account_ids: List[str]


class AccountInfoResponse(BaseModel):
    address: str
    balance: int
    status: str


class BulkAccountsResponse(BaseModel):
    accounts: List[AccountInfoResponse]
```

### Creating namespaces

Use `APINamespace` to group related endpoints logically.

```python
class Accounts(APINamespace):
    path = "accounts"

    @endpoint("GET", path="{account_id}", model=AccountInfoResponse)
    async def info(self, account_id: str) -> AccountInfoResponse:
        """
        Retrieve account information.
        GET /accounts/{account_id}
        """
        pass

    @endpoint("POST", path="_bulk", model=BulkAccountsResponse)
    async def bulk_info(self, body: BulkAccountsRequest) -> BulkAccountsResponse:
        """
        Retrieve information for multiple accounts with Pydantic body and response model.
        POST /accounts/_bulk
        """
        pass

    @endpoint("POST", path="_bulk")
    async def bulk_info_dict(self, body: dict) -> dict:
        """
        Retrieve information for multiple accounts with dict body and dict response.
        POST /accounts/_bulk
        """
        pass
```

### Adding standalone endpoints

Endpoints can also be defined directly within your client class.

* If `path` is not specified, the method name will be used as the endpoint path automatically (e.g. `status` →
  `/status`).

```python
class TONAPI(APIClient):
    url = "https://tonapi.io"
    version = "v2"

    @endpoint("GET")
    async def status(self) -> dict:
        """
        Check API status.
        GET /status
        Returns a dict since no response model is specified.
        """
        pass

    @endpoint("GET")
    async def rates(self, tokens: str, currencies: str) -> dict:
        """
        Get token rates.
        GET /rates?tokens={tokens}&currencies={currencies}
        """
        pass

    @property
    def accounts(self) -> Accounts:
        return Accounts(self)
```

### Calling endpoints

Example usage demonstrating:

* Positional and keyword arguments.
* POST body as either a Pydantic model or dict.
* Returning raw dict responses when no model is defined.

```python
async def main():
    tonapi = TONAPI(rps=1, debug=True)

    # GET /status
    status = await tonapi.status()

    # GET /rates with positional arguments
    rates_positional = await tonapi.rates("ton", "usd")

    # GET /rates with keyword arguments
    rates_keyword = await tonapi.rates(tokens="ton", currencies="usd")

    # GET /accounts/{account_id} with positional argument
    account_positional = await tonapi.accounts.info("UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0")

    # GET /accounts/{account_id} with keyword argument
    account_keyword = await tonapi.accounts.info(account_id="UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0")

    # POST /accounts/_bulk with a Pydantic model body and response
    accounts_bulk_model = await tonapi.accounts.bulk_info(
        body=BulkAccountsRequest(
            account_ids=[
                "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0",
                "UQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNbbp",
            ]
        )
    )

    # POST /accounts/_bulk with a dict body and response
    accounts_bulk_dict = await tonapi.accounts.bulk_info_dict(
        body={
            "account_ids": [
                "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0",
                "UQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNbbp",
            ]
        }
    )

    print("Status:", status)
    print("Rates (positional):", rates_positional)
    print("Rates (keyword):", rates_keyword)
    print("Account (positional):", account_positional)
    print("Account (keyword):", account_keyword)
    print("Bulk accounts (model):", accounts_bulk_model)
    print("Bulk accounts (dict):", accounts_bulk_dict)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
```

### Notes

* **POST body payloads** can be provided as Pydantic models or plain dicts.
* If no `model` is specified in `@endpoint`, the raw dict response is returned.
* If `path` is not specified in `@endpoint`, it defaults to the method name as the endpoint path.

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## License

This repository is distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.
