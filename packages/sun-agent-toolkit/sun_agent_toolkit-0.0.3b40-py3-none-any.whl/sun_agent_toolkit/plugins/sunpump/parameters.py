from pydantic import BaseModel, Field


class SearchTokenParameters(BaseModel):
    symbol: str = Field(description="The token symbol")
    top_n: int = Field(description="max num of tokens to be returned", default=10)


class GetTokenLaunchStatusParameters(BaseModel):
    token_address: str = Field(description="The token address")


class TokenLaunchParameters(BaseModel):
    name: str = Field(description="The name of token")
    symbol: str = Field(description="The symbol of token")
    description: str = Field(description="The description of token")
    imageBase64: str = Field(description="The image of token, base64 encoded")
    ownerAddress: str = Field(description="The address of whom wants to create this token")
    initialBuy: float = Field(description="The amount to buy once the token is created. default to 0", default=0)
    twitterUrl: str | None = Field(description="twitter url [optional]")
    telegramUrl: str | None = Field(description="telegram url [optional]")
    websiteUrl: str | None = Field(description="website url [optional]")


class GetFeesParameters(BaseModel):
    pass


class GetTokenParameters(BaseModel):
    contractAddress: str = Field(description="SunPump token contract address")


class GetRankingParameters(BaseModel):
    rankingType: str = Field(
        description="Ranking type: PUMP_PERCENT | MARKET_CAP | PRICE_CHANGE_24H | VOLUME_24H",
        default="PRICE_CHANGE_24H",
        pattern="^(PUMP_PERCENT|MARKET_CAP|PRICE_CHANGE_24H|VOLUME_24H)$",
    )
    limit: int = Field(default=10, description="Number of items to return (max 50)")
