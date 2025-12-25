from pydantic import BaseModel, Field


class SwapTokensParameters(BaseModel):
    fromToken: str = Field(description="Input token address (Base58)")
    toToken: str = Field(description="Output token address (Base58)")
    amountIn: str = Field(description="Exact input amount in base units (sun)")
    slippageTolerance: float | None = Field(default=0.005, description="Slippage tolerance (default 0.5%)")


class RouterParameters(BaseModel):
    fromToken: str = Field(description="fromToken address (Base58)")
    toToken: str = Field(description="toToken address (Base58)")
    amountIn: str = Field(description="Exact input amount in base units (sun)")


class EstimateEnergyParameters(BaseModel):
    fromToken: str = Field(description="fromToken address (Base58)")
    toToken: str = Field(description="toToken address (Base58)")
    amountIn: str = Field(description="Exact input amount in base units (sun)")
    slippageTolerance: float | None = Field(default=0.005, description="Slippage tolerance (default 0.5%)")


class PurchaseSunPumpTokenParameters(BaseModel):
    token_address: str = Field(description="SunPump token address (Base58)")
    trx_amount: str = Field(description="TRX amount to spend (human-readable, e.g., '10')")
    amount_out_min: str = Field(default="0", description="Minimum token amount to receive (human-readable)")
    slippage_tolerance: float = Field(default=0.01, description="Slippage tolerance (default 1%)")


class SaleSunPumpTokenParameters(BaseModel):
    token_address: str = Field(description="SunPump token address (Base58)")
    token_amount: str = Field(description="Token amount to sell (human-readable)")
    amount_out_min: str = Field(default="0", description="Minimum TRX amount to receive (human-readable)")
    slippage_tolerance: float = Field(default=0.01, description="Slippage tolerance (default 1%)")
