from typing import List

from pydantic import BaseModel

from apiq import apiclient, apinamespace, endpoint


class BulkAccountsRequest(BaseModel):
    account_ids: List[str]


class AccountInfoResponse(BaseModel):
    address: str
    balance: int
    status: str


class BulkAccountsResponse(BaseModel):
    accounts: List[AccountInfoResponse]


@apinamespace("accounts")
class Accounts:

    @endpoint("GET", path="/{account_id}", as_model=AccountInfoResponse)
    async def info(self, account_id: str) -> AccountInfoResponse:
        """Retrieve account information by account_id (GET /accounts/{account_id})"""

    @endpoint("POST", path="/_bulk", as_model=BulkAccountsResponse)
    async def bulk_info(self, body: BulkAccountsRequest) -> BulkAccountsResponse:
        """Retrieve info for multiple accounts with a Pydantic model (POST /accounts/_bulk)"""

    @endpoint("POST", path="/_bulk")
    async def bulk_info_dict(self, body: dict) -> dict:
        """Retrieve info for multiple accounts with a dict payload (POST /accounts/_bulk)"""


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

    @property
    def accounts(self) -> Accounts:
        return Accounts(self)


async def main():
    tonapi = TONAPI()

    async with tonapi:
        # GET /status
        status = await tonapi.status()

        # GET /rates (with positional and keyword arguments)
        rates_positional = await tonapi.rates("ton", "usd")
        rates_keyword = await tonapi.rates(tokens="ton", currencies="usd")

        # GET /accounts/{account_id} (with positional and keyword arguments)
        account_positional = await tonapi.accounts.info("UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0")
        account_keyword = await tonapi.accounts.info(account_id="UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0")

        # POST /accounts/_bulk (with a Pydantic model body)
        accounts_bulk_model = await tonapi.accounts.bulk_info(
            body=BulkAccountsRequest(
                account_ids=[
                    "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0",
                    "UQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNbbp",
                ]
            )
        )
        # POST /accounts/_bulk (with a dict body)
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

    asyncio.run(main())
