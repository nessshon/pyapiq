from typing import List

from pydantic import BaseModel

from pyapiq import AsyncClientAPI, AsyncAPINamespace, async_endpoint
from pyapiq.types import HTTPMethod


class BulkAccountsRequest(BaseModel):
    account_ids: List[str]


class AccountInfoResponse(BaseModel):
    address: str
    balance: int
    status: str


class BulkAccountsResponse(BaseModel):
    accounts: List[AccountInfoResponse]


class Accounts(AsyncAPINamespace):
    namespace = "accounts"

    @async_endpoint(HTTPMethod.GET, path="/{account_id}", return_as=AccountInfoResponse)
    async def info(self, account_id: str) -> AccountInfoResponse:
        """Retrieve account information by account_id (GET /accounts/{account_id})"""

    @async_endpoint(HTTPMethod.POST, path="/_bulk", return_as=BulkAccountsResponse)
    async def bulk_info(self, payload: BulkAccountsRequest) -> BulkAccountsResponse:
        """Retrieve info for multiple accounts with a Pydantic model (POST /accounts/_bulk)"""

    @async_endpoint(HTTPMethod.POST, path="/_bulk")
    async def bulk_info_dict(self, payload: dict) -> dict:
        """Retrieve info for multiple accounts with a dict payload (POST /accounts/_bulk)"""


class AsyncTONAPI(AsyncClientAPI):
    base_url = "https://tonapi.io"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    version = "v2"
    rps = 1
    max_retries = 2

    @async_endpoint(HTTPMethod.GET)
    async def status(self) -> dict:
        """Check API status (GET /status)"""

    @async_endpoint(HTTPMethod.GET)
    async def rates(self, tokens: str, currencies: str) -> dict:
        """Get token rates (GET /rates?tokens={tokens}&currencies={currencies})"""

    @property
    def accounts(self) -> Accounts:
        return Accounts(self)


async def main():
    tonapi = AsyncTONAPI()

    async with tonapi:
        # GET /status
        status = await tonapi.status()

        # GET /rates (with positional and keyword arguments)
        rates_positional = await tonapi.rates("ton", "usd")
        rates_keyword = await tonapi.rates(tokens="ton", currencies="usd")

        # GET /accounts/{account_id} (with positional and keyword arguments)
        account_positional = await tonapi.accounts.info(
            "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0"
        )
        account_keyword = await tonapi.accounts.info(
            account_id="UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0"
        )

        # POST /accounts/_bulk (with a Pydantic model payload)
        accounts_bulk_model = await tonapi.accounts.bulk_info(
            payload=BulkAccountsRequest(
                account_ids=[
                    "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0",
                    "UQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNbbp",
                ]
            )
        )
        # POST /accounts/_bulk (with a dict payload)
        accounts_bulk_dict = await tonapi.accounts.bulk_info_dict(
            payload={
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

    asyncio.run(main())
