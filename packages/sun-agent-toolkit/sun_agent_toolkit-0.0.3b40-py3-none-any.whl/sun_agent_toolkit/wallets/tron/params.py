from typing import Any, Literal

from pydantic import BaseModel, Field


class GetBalanceParameters(BaseModel):
    """Parameters for getting balance"""

    address: str = Field(description="The TRON address to check balance for")
    tokenAddress: str | None = Field(
        description="The TRC20 token address to check balance for, omit for TRX", default=None
    )


class GetTokenInfoBySymbolParameters(BaseModel):
    """Parameters for getting token info by symbol"""

    symbol: str = Field(description="The token symbol to get information for (e.g., USDT, USDC)")
    network: str = Field(description="The TRON network (mainnet, shasta, nile)", default="mainnet")


class GetTokenInfoByAddressParameters(BaseModel):
    """Parameters for getting token info by address(EVM compatible)"""

    address: str | None = Field(
        description="The token base58 address to get information for, None for native token", default=None
    )


class GetTokenInfoByTickerParameters(BaseModel):
    """Parameters for getting token info by ticker (EVM compatible)"""

    ticker: str = Field(description="The token ticker symbol to get information for (e.g., USDT, USDC)")


class ConvertToSunParameters(BaseModel):
    """Parameters for converting TRX to SUN (smallest unit)"""

    amount: str = Field(description="The amount of TRX to convert to SUN")


class ConvertFromSunParameters(BaseModel):
    """Parameters for converting SUN to TRX"""

    amount: str = Field(description="The amount in SUN to convert to TRX")


class ConvertToBaseUnitsParameters(BaseModel):
    """Parameters for converting tokens to base units"""

    amount: str = Field(description="The amount of tokens to convert to base units")
    tokenAddress: str | None = Field(description="The token address to convert for, omit for TRX", default=None)


class ConvertFromBaseUnitsParameters(BaseModel):
    """Parameters for converting from base units to human-readable format"""

    amount: str = Field(description="The amount in base units to convert to human-readable format")
    tokenAddress: str | None = Field(description="The token address to convert for, omit for TRX", default=None)


class SendTokenParameters(BaseModel):
    """Parameters for sending tokens"""

    recipient: str = Field(description="The TRON address to send tokens to")
    amountInBaseUnits: str = Field(
        description="The amount of tokens to send in base units (SUN for TRX, smallest unit for TRC20)"
    )
    tokenAddress: str | None = Field(description="The TRC20 token address to send, omit for TRX", default=None)


class GetTokenAllowanceParameters(BaseModel):
    """Parameters for getting token allowance"""

    tokenAddress: str = Field(description="The TRC20 token address to check allowance for")
    owner: str = Field(description="The owner address")
    spender: str = Field(description="The spender address")


class ApproveParameters(BaseModel):
    """Parameters for approving token spending"""

    tokenAddress: str = Field(description="The TRC20 token address to approve")
    spender: str = Field(description="The spender address to approve")
    amount: str = Field(description="The amount to approve in base units")


class RevokeApprovalParameters(BaseModel):
    """Parameters for revoking token approval"""

    tokenAddress: str = Field(description="The TRC20 token address to revoke approval for")
    spender: str = Field(description="The spender address to revoke approval from")


class TriggerSmartContractParameters(BaseModel):
    """Parameters for triggering smart contract"""

    contractAddress: str = Field(description="The smart contract address")
    functionSelector: str = Field(description="The function selector (first 4 bytes of function signature hash)")
    parameter: str = Field(description="The encoded parameters for the function call")
    feeLimit: int | None = Field(description="Maximum energy fee in SUN", default=1_000_000)
    callValue: int | None = Field(description="TRX amount to send with the call in SUN", default=0)


class BuildSendTrxParameters(BaseModel):
    """Parameters for building an unsigned TRX transfer transaction"""

    to: str = Field(description="The recipient address in base58 or hex format")
    amount: int = Field(description="Amount of TRX to send, expressed in SUN")
    from_address: str | None = Field(
        description="Optional sender address. Defaults to the wallet address if omitted.",
        default=None,
    )
    options: dict[str, Any] | None = Field(
        description="Optional transaction options such as feeLimit, permissionId, memo, or expiration.",
        default=None,
    )


class BuildSendTokenParameters(BaseModel):
    """Parameters for building an unsigned TRC20 token transfer transaction"""

    to: str = Field(description="The recipient address in base58 or hex format")
    amount: int = Field(description="Amount of tokens to send, expressed in base units")
    tokenId: str = Field(
        description="The TRC20 token contract address or identifier",
    )
    from_address: str | None = Field(
        description="Optional sender address. Defaults to the wallet address if omitted.",
        default=None,
    )
    options: dict[str, Any] | None = Field(
        description="Optional transaction options such as feeLimit, permissionId, memo, or expiration.",
        default=None,
    )


class SignTransactionParameters(BaseModel):
    """Parameters for signing a TRON transaction"""

    transaction: dict[str, Any] | str = Field(
        description="The transaction object to sign, or its JSON string representation"
    )


class SendRawTransactionParameters(BaseModel):
    """Parameters for broadcasting a signed TRON transaction"""

    signedTransaction: dict[str, Any] | str = Field(
        description="The signed transaction object or its JSON string representation"
    )


class SignMessageParameters(BaseModel):
    """Parameters for signing messages"""

    message: str = Field(description="The message to sign")


class SignTypedDataParameters(BaseModel):
    """Parameters for signing typed data (EIP-712 compatible for TRON)"""

    types: dict[str, Any] = Field(description="The type definitions for the typed data")
    primaryType: str = Field(description="The primary type of the typed data")
    domain: dict[str, Any] = Field(description="The domain separator for the typed data")
    value: dict[str, Any] = Field(description="The actual data to sign")


class GetTransactionParameters(BaseModel):
    """Parameters for getting transaction details"""

    txHash: str = Field(description="The transaction hash to get details for")


class GetAccountInfoParameters(BaseModel):
    """Parameters for getting account information"""

    address: str | None = Field(description="The TRON address to get account info for, None for user wallet address")


class UnfreezeBalanceParameters(BaseModel):
    """Parameters for unstaking balance (Stake 2.0)."""

    resource: Literal["ENERGY", "BANDWIDTH"] = Field(description='Resource type to unfreeze, "ENERGY" or "BANDWIDTH"')
    amountInSun: str | None = Field(
        description="Amount to unfreeze in SUN.",
        default=None,
    )


class WithdrawStakeBalanceParameters(BaseModel):
    """Parameters for withdrawing expired unstaked TRX (after cool-down)."""

    # No parameters required; uses wallet owner address
    pass


class DelegateResourceParameters(BaseModel):
    """Parameters for delegating ENERGY/BANDWIDTH to another address (Stake 2.0)."""

    receiver: str = Field(description="Receiver address to delegate resources to")
    amountInSun: str = Field(description="Amount of resources (in SUN) to delegate")
    resource: Literal["ENERGY", "BANDWIDTH"] = Field(description='Resource type, "ENERGY" or "BANDWIDTH"')
    lock: bool = Field(description="Whether to lock delegated resources for 3 days", default=False)


class UndelegateResourceParameters(BaseModel):
    """Parameters for cancelling delegation (Stake 2.0)."""

    receiver: str = Field(description="Receiver address to cancel delegation from")
    amountInSun: str = Field(description="Amount of resources (in SUN) to undelegate")
    resource: Literal["ENERGY", "BANDWIDTH"] = Field(description='Resource type, "ENERGY" or "BANDWIDTH"')


class VoteWitnessParameters(BaseModel):
    """Parameters for voting witnesses (governance)."""

    votes: list[dict[str, Any]] = Field(
        description=(
            "List of vote entries. Each entry requires keys: "
            "'witnessAddress' (str, SR address) and 'voteCount' (int, number of votes)."
        )
    )


class WithdrawRewardsParameters(BaseModel):
    """Parameters for withdrawing voting rewards."""

    # No parameters required; uses wallet owner address
    pass


class FreezeBalanceParameters(BaseModel):
    """Parameters for freezing balance to obtain ENERGY or BANDWIDTH (Stake 2.0)."""

    amountInSun: str = Field(description="Amount of TRX to freeze in SUN (1 TRX = 1_000_000 SUN)")
    resource: Literal["ENERGY", "BANDWIDTH"] = Field(description='Resource type to obtain, "ENERGY" or "BANDWIDTH"')


class GetAccountResourceInfoParameters(BaseModel):
    """Parameters for getting account resource info (energy/bandwidth)."""

    # No parameters required; uses wallet owner address
    pass


class GetVotesParameters(BaseModel):
    """Parameters for getting current witness votes of the account."""

    # No parameters required; uses wallet owner address
    pass


class GetPendingRewardParameters(BaseModel):
    """Parameters for getting pending reward (in SUN)."""

    # No parameters required; uses wallet owner address
    pass


class GetStakeInfoParameters(BaseModel):
    """Parameters for getting stake information."""

    # No parameters required; uses wallet owner address
    pass


class GetDelegatedResourceParameters(BaseModel):
    "Parameters for get the info of delegated resource"

    to_address: str = Field(description="the address of resource delegate to")
    from_address: str | None = Field(description="the address of resource delegate from")
