from pydantic import BaseModel, Field


class GetAccountInfoParameters(BaseModel):
    address: str = Field(description="The TRON address to get account information for")
    include_tokens: bool | None = Field(default=True, description="Include TRC20 token balances in the response")


class GetWitnessesParameters(BaseModel):
    witness_type: int = Field(
        description="The type of witness to be returned. 0: Witness 1: Partner 3: Candidate, Default: 0", default=0
    )
    top_n: int = Field(description="max num of witnesses to be returned", default=10)


class GetTransactionParameters(BaseModel):
    tx_hash: str = Field(description="The transaction hash to get details for")


class GetAccountTransactionsParameters(BaseModel):
    address: str = Field(description="The TRON address to get transactions for")
    limit: int | None = Field(default=20, description="The number of transactions to return (max 200)")
    start: int | None = Field(default=0, description="The starting index for pagination")
    sort: str | None = Field(
        default="-timestamp", description="Sort order: -timestamp (newest first) or timestamp (oldest first)"
    )
    only_confirmed: bool | None = Field(default=True, description="Only return confirmed transactions")


class GetTokenInfoParameters(BaseModel):
    contract_address: str = Field(description="The TRC20 token contract address")


class GetTokenHoldersParameters(BaseModel):
    contract_address: str = Field(description="The TRC20 token contract address")
    limit: int = Field(default=20, description="The number of holders to return (max 100)")
    start: int = Field(default=0, description="The starting index for pagination")


class GetTronStatsParameters(BaseModel):
    """Get TRON network statistics"""

    pass


class SearchTronParameters(BaseModel):
    search_key: str = Field(description="Search keyword (address, tx hash, token/contract name, block number)")
    search_type: str = Field(
        default="token",
        description="Search type filter: token | address | contract | transaction | block (default: token)",
        pattern="^(token|address|contract|transaction|block)$",
    )


class GetTokenMarketParameters(BaseModel):
    token: str = Field(description="TRC20 token contract address")


class GetRankingParameters(BaseModel):
    sortBy: str = Field(
        default="marketcap",
        description="Sorting field (TronScan /tokens/overview): priceInTrx | gain | volume24hInTrx | holderCount | marketCapUsd",
        pattern="^(priceInTrx|gain|volume24hInTrx|holderCount|marketCapUsd)$",
    )
    order: str = Field(default="desc", description="Sorting order: asc | desc (default desc)", pattern="^(asc|desc)$")
    limit: int = Field(default=10, description="Number of ranking items to return (max 500)")
