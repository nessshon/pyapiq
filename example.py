import logging
from typing import List

from pydantic import BaseModel
from apiq import APINamespace, endpoint, APIClient


class BulkAccountsRequest(BaseModel):
    account_ids: List[str]


class AccountInfoResponse(BaseModel):
    address: str
    balance: int
    status: str


class BulkAccountsResponse(BaseModel):
    accounts: List[AccountInfoResponse]


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


class TONAPI(APIClient):
    url = "https://tonapi.io"
    version = "v2"

    @endpoint("GET")
    async def status(self) -> dict:
        """
        Check API status.
        GET /status
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
