import re
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from sun_agent_toolkit.core.classes.tool_base import ToolBase, create_tool
from sun_agent_toolkit.core.classes.wallet_client_base import Balance, Signature, WalletClientBase
from sun_agent_toolkit.core.types.chain import TronChain
from sun_agent_toolkit.core.types.token import Token

from .abi import TRC20_ABI
from .params import (
    ApproveParameters,
    ConvertFromBaseUnitsParameters,
    ConvertToBaseUnitsParameters,
    DelegateResourceParameters,
    FreezeBalanceParameters,
    GetAccountInfoParameters,
    GetAccountResourceInfoParameters,
    GetBalanceParameters,
    GetDelegatedResourceParameters,
    GetPendingRewardParameters,
    GetStakeInfoParameters,
    GetTokenAllowanceParameters,
    GetTokenInfoByAddressParameters,
    GetTokenInfoByTickerParameters,
    GetVotesParameters,
    RevokeApprovalParameters,
    SendTokenParameters,
    SignTypedDataParameters,
    UndelegateResourceParameters,
    UnfreezeBalanceParameters,
    VoteWitnessParameters,
    WithdrawRewardsParameters,
    WithdrawStakeBalanceParameters,
)
from .tokens import SUNSWAP_TOKEN_LIST, TronToken
from .types import TronReadRequest, TronReadResult, TronTransaction


class TronOptions:
    """Configuration options for TRON wallet clients."""

    def __init__(self) -> None:
        pass


class TronWalletBase(WalletClientBase, ABC):
    """Base class for TRON wallet implementations."""

    def __init__(self, tokens: list[TronToken] | None = None, enable_send: bool = True) -> None:
        """Initialize the TRON wallet client.

        Args:
            tokens: List of token configurations
            enable_send: Whether to enable send functionality
        """
        WalletClientBase.__init__(self)
        self.tokens = tokens or SUNSWAP_TOKEN_LIST
        self.enable_send = enable_send

    def get_chain(self) -> TronChain:
        """Get the chain type for TRON."""
        network = self.get_network_id()
        return TronChain(network)

    @abstractmethod
    def get_address(self) -> str:
        """Get the wallet's public address."""
        pass

    @abstractmethod
    def get_network_id(self) -> str:
        """Get the network ID (e.g., 'mainnet', 'shasta', 'nile')."""
        pass

    @abstractmethod
    def get_transaction_url(self, tx_hash: str) -> str:
        """Get the tronscan url of transaction"""
        pass

    @abstractmethod
    async def get_transaction_receipt(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get the receipt of transaction"""
        pass

    @abstractmethod
    async def sign_message(self, message: str) -> Signature:
        """Sign a message with the wallet's private key."""
        pass

    @abstractmethod
    async def sign_typed_data(
        self, types: dict[str, Any], primary_type: str, domain: dict[str, Any], value: dict[str, Any]
    ) -> Signature:
        """Sign typed data with the wallet's private key (TRON equivalent of EIP-712)."""
        pass

    @abstractmethod
    async def send_transaction(self, transaction: TronTransaction) -> dict[str, str]:
        """Send a transaction on the TRON chain."""
        pass

    @abstractmethod
    def read(self, request: TronReadRequest) -> TronReadResult:
        """Read data from a smart contract."""
        pass

    @abstractmethod
    def get_native_balance(self) -> int:
        """Get the native balance of the wallet in SUN."""
        pass

    @abstractmethod
    def get_account_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """Account info in details."""
        pass

    @abstractmethod
    def get_account_resource_info(self) -> dict[str, Any]:
        """Account resource info (energy/bandwidth)."""
        pass

    @abstractmethod
    def get_votes(self) -> dict[str, int]:
        """Get voting stats: totalVotes, usedVotes, availableVotes."""
        pass

    @abstractmethod
    def get_pending_reward(self) -> int:
        """Pending reward in SUN."""
        pass

    @abstractmethod
    def get_stake_info(self) -> dict[str, Any]:
        """Stake 2.0 信息，包括质押与委托数据。"""
        pass

    # ----- Stake 2.0 & Governance (abstract API to be implemented by concrete client) -----

    @abstractmethod
    async def freeze_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Freeze TRX to obtain ENERGY or BANDWIDTH (Stake 2.0)."""
        pass

    @abstractmethod
    async def unfreeze_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Unstake TRX (Stake 2.0)."""
        pass

    @abstractmethod
    async def withdraw_stake_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Withdraw expired unstaked TRX after cool-down period (Stake 2.0)."""
        pass

    @abstractmethod
    async def delegate_resource(self, params: dict[str, Any]) -> dict[str, str]:
        """Delegate ENERGY/BANDWIDTH to another address (Stake 2.0)."""
        pass

    @abstractmethod
    async def undelegate_resource(self, params: dict[str, Any]) -> dict[str, str]:
        """Cancel delegation of ENERGY/BANDWIDTH (Stake 2.0)."""
        pass

    @abstractmethod
    async def vote_witness(self, params: dict[str, Any]) -> dict[str, str]:
        """Vote for witnesses (governance)."""
        pass

    @abstractmethod
    async def withdraw_rewards(self, params: dict[str, Any]) -> dict[str, str]:
        """Withdraw voting rewards."""
        pass

    @abstractmethod
    def balance_of(self, address: str, token_address: str | None = None) -> Balance:
        """Get the balance of an address for native or TRC20 tokens.

        Args:
            address: The address to check balance for
            token_address: Optional TRC20 token address

        Returns:
            Balance information
        """
        pass

    @abstractmethod
    def get_token_info_by_address(self, address: str) -> Token:
        """Get token information by token address.

        Args:
            address: The token base58 address

        Returns:
            Token information
        """
        pass

    @abstractmethod
    def get_token_info_by_ticker(self, ticker: str) -> Token:
        """Get token information by ticker symbol.

        Args:
            ticker: The token ticker symbol (e.g., USDT, USDC)

        Returns:
            Token information
        """
        pass

    @abstractmethod
    def get_delegated_resource(self, params: dict[str, Any]) -> dict[str, Any]:
        pass

    def _get_token_decimals(self, token_address: str | None = None) -> int:
        """Get the decimals for a token.

        Args:
            token_address: The token address, or None for native currency

        Returns:
            Number of decimals
        """
        if token_address is None or token_address == "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb":
            return 6
        network = self.get_network_id()
        for token in self.tokens:
            if network not in token["networks"] or token_address != token["networks"][network]["contractAddress"]:
                continue
            return token["decimals"]
        try:
            decimals_result = self.read(
                {"address": token_address, "abi": TRC20_ABI, "functionName": "decimals", "args": []}
            )
            return int(decimals_result["value"])
        except Exception as e:
            raise ValueError(f"Failed to fetch token decimals: {str(e)}") from e

    def convert_to_base_units(self, params: dict[str, Any]) -> str:
        """Convert a token amount to base units.

        Args:
            params: Parameters including amount and optional token address

        Returns:
            Amount in base units
        """
        amount = params["amount"]
        token_address = params.get("tokenAddress")

        TRX_NATIVE_ADDR = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"  # mainnet/nile 通用占位
        if token_address == TRX_NATIVE_ADDR:
            token_address = None

        try:
            decimals = self._get_token_decimals(token_address)
            base_units = int(Decimal(amount) * (10**decimals))
            return str(base_units)
        except Exception as e:
            raise ValueError(f"Failed to convert to base units: {str(e)}") from e

    def convert_from_base_units(self, params: dict[str, Any]) -> str:
        """Convert a token amount from base units to decimal.

        Args:
            params: Parameters including amount and optional token address

        Returns:
            Human-readable amount
        """
        amount = params["amount"]
        token_address = params.get("tokenAddress")

        # 原生 TRX 同样按 6 位精度处理（同上别名集合规则），无需区分网络
        TRX_NATIVE_ADDR = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"
        ZERO_HEX = "0x0000000000000000000000000000000000000000"
        native_aliases = {None, "", ZERO_HEX, TRX_NATIVE_ADDR}
        if token_address in native_aliases:
            token_address = None

        try:
            if not re.match(r"^[0-9]+$", amount):
                raise ValueError(f"Invalid base unit amount format: {amount}")

            decimals = self._get_token_decimals(token_address)
            decimal_amount = Decimal(amount) / (10**decimals)
            return str(decimal_amount)
        except Exception as e:
            raise ValueError(f"Failed to convert from base units: {str(e)}") from e

    async def send_token(self, params: dict[str, Any]) -> dict[str, str]:
        """Send tokens (native or TRC20).

        Args:
            params: Parameters including recipient, amount, and optional token address

        Returns:
            Transaction receipt
        """
        if not self.enable_send:
            raise ValueError("Sending tokens is disabled for this wallet")

        recipient = params["recipient"]
        amount_in_base_units = params["amountInBaseUnits"]
        token_address = params.get("tokenAddress")

        try:
            if token_address and token_address != "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb":
                return await self.send_transaction(
                    {
                        "to": token_address,
                        "abi": TRC20_ABI,
                        "functionName": "transfer",
                        "args": [recipient, int(amount_in_base_units)],
                    }
                )
            else:
                return await self.send_transaction(
                    {
                        "to": recipient,
                        "value": int(amount_in_base_units),
                    }
                )
        except Exception as e:
            raise ValueError(f"Failed to send token: {str(e)}") from e

    def get_token_allowance(self, params: dict[str, Any]) -> str:
        """Get the allowance of a TRC20 token for a spender.

        Args:
            params: Parameters including token address, owner, and spender

        Returns:
            Allowance in base units
        """
        token_address = params["tokenAddress"]
        owner = params["owner"]
        spender = params["spender"]

        try:
            allowance_result = self.read(
                {
                    "address": token_address,
                    "abi": TRC20_ABI,
                    "functionName": "allowance",
                    "args": [owner, spender],
                }
            )
            return str(allowance_result["value"])
        except Exception as e:
            raise ValueError(f"Failed to fetch allowance: {str(e)}") from e

    async def approve(self, params: dict[str, Any]) -> dict[str, str]:
        """Approve a spender to spend TRC20 tokens.

        Args:
            params: Parameters including token address, spender, and amount

        Returns:
            Transaction receipt
        """
        if not self.enable_send:
            raise ValueError("Approval operations are disabled for this wallet")

        token_address = params["tokenAddress"]
        spender = params["spender"]
        amount = params["amount"]

        try:
            if not re.match(r"^[0-9]+$", amount):
                raise ValueError(f"Invalid base unit amount format: {amount}")

            return await self.send_transaction(
                {
                    "to": token_address,
                    "abi": TRC20_ABI,
                    "functionName": "approve",
                    "args": [spender, int(amount)],
                }
            )
        except Exception as e:
            raise ValueError(f"Failed to approve: {str(e)}") from e

    async def revoke_approval(self, params: dict[str, Any]) -> dict[str, str]:
        """Revoke approval for a TRC20 token from a spender.

        Args:
            params: Parameters including token address and spender

        Returns:
            Transaction receipt
        """
        return await self.approve(
            {
                "tokenAddress": params["tokenAddress"],
                "spender": params["spender"],
                "amount": "0",
            }
        )

    def get_core_tools(self) -> list[ToolBase[Any]]:
        """Get the core tools for this wallet client.

        Returns:
            List of tool definitions
        """
        base_tools = [
            tool for tool in super().get_core_tools() if tool.name != "get_balance"
        ]  # we override the get_balance tool

        common_tron_tools = [
            create_tool(
                {
                    "name": "get_balance",
                    "description": "Get the balance of the wallet for native currency or a specific TRC20 token.",
                    "parameters": GetBalanceParameters,
                },
                lambda params: self.balance_of(params["address"], params.get("tokenAddress")),
            ),
            create_tool(
                {
                    "name": "get_token_info_by_ticker",
                    "description": "Get basic information(address, name, symbol, decimals) about a token by its ticker symbol.",
                    "parameters": GetTokenInfoByTickerParameters,
                },
                lambda params: self.get_token_info_by_ticker(params["ticker"]),
            ),
            create_tool(
                {
                    "name": "get_token_info_by_address",
                    "description": "Get basic information(address, name, symbol, decimals) about a token by its contract address.",
                    "parameters": GetTokenInfoByAddressParameters,
                },
                lambda params: self.get_token_info_by_address(params["address"]),
            ),
            create_tool(
                {
                    "name": "convert_to_base_units",
                    "description": "Convert a token amount from human-readable units to base units.",
                    "parameters": ConvertToBaseUnitsParameters,
                },
                self.convert_to_base_units,
            ),
            create_tool(
                {
                    "name": "convert_from_base_units",
                    "description": "Convert a token amount from base units to human-readable units.",
                    "parameters": ConvertFromBaseUnitsParameters,
                },
                self.convert_from_base_units,
            ),
            create_tool(
                {
                    "name": "get_token_allowance_tron",
                    "description": "Get the allowance of a TRC20 token for a spender.",
                    "parameters": GetTokenAllowanceParameters,
                },
                self.get_token_allowance,
            ),
            create_tool(
                {
                    "name": "sign_typed_data_tron",
                    "description": "Sign a typed data structure (TRON equivalent of EIP-712).",
                    "parameters": SignTypedDataParameters,
                },
                lambda params: self.sign_typed_data(
                    params["types"], params["primaryType"], params["domain"], params["value"]
                ),
            ),
            create_tool(
                {
                    "name": "get_account_info",
                    "description": "Get account info in details.",
                    "parameters": GetAccountInfoParameters,
                },
                self.get_account_info,
            ),
            create_tool(
                {
                    "name": "get_account_resource_info",
                    "description": """Get account resource info (energy/bandwidth).
output description:
- TotalEnergyWeight: The total TRX staked for energy by all accounts across the entire blockchain.
- TotalEnergyLimit: The total energy supply available across the entire blockchain.
- TotalNetWeight: The total TRX staked for bandwidth by all accounts across the entire blockchain.
- TotalNetLimit: The total bandwidth supply available across the entire blockchain.
- freeNetUsed: The amount of free bandwidth used by this account.
- freeNetLimit: The daily free bandwidth limit for this account.
- NetUsed: The amount of bandwidth used by this account that was obtained by staking TRX (Stake 2.0).
- NetLimit: The total bandwidth this account has from staking TRX (Stake 2.0), excluding any amount delegated to others.
- NetUsedIncludeFree: the total bandwidth used by this account(freeNetUsed + NetUsed), this is preferred when query bandwidth usage of user's account.
- NetLimitIncludeFree: the total bandwidth of this account(freeNetLimit + NetLimit), this is preferred when query bandwidth of user's amount.
- EnergyUsed: The amount of energy used by this account that was obtained by staking TRX (Stake 2.0).
- EnergyLimit: The total energy this account has from staking TRX (Stake 2.0), excluding any amount delegated to others.
- tronPowerUsed: The amount of vote power (Tron Power) used by this account for voting for Super Representatives.
- tronPowerLimit: The total vote power (Tron Power) of this account, which is 1:1 with staked TRX.
- assetNetUsed: A list of TRC-10 token bandwidth used by the account. The 'key' is the token ID and 'value' is the amount used.
- assetNetLimit: A list of TRC-10 token bandwidth limits for the account. The 'key' is the token ID and 'value' is the limit.
""",
                    "parameters": GetAccountResourceInfoParameters,
                },
                lambda _params: self.get_account_resource_info(),
            ),
            create_tool(
                {
                    "name": "get_votes",
                    "description": "Get voting stats: totalVotes, usedVotes, availableVotes.",
                    "parameters": GetVotesParameters,
                },
                lambda _params: self.get_votes(),
            ),
            create_tool(
                {
                    "name": "get_pending_reward",
                    "description": """Get claimable TRX reward amount that was obtained by voting.
output description:
- int, the amount of TRX reward that is in base units, not human readable.
""",
                    "parameters": GetPendingRewardParameters,
                },
                lambda _params: self.get_pending_reward(),
            ),
            create_tool(
                {
                    "name": "get_stake_info",
                    "description": """Get stake 2.0 information including frozen and delegated resources.
output description:
- tronPower: The total vote power (Tron Power) of this account, which is 1:1 with staked TRX.
- frozen: the detail of staked trx(in base units) that can be unstaked
- totalFrozen: the staked trx amount(in base units) can be unstaked
- totalFrozenIncludeDelegated: the total staked trx amount(readable) including that is delegated to others
- frozenByResource: the staked trx amount(in base units) can be unstaked group by resource type
- totalDelegatedOut: the trx amount(in base units) that is delegated to others
- delegatedOutByResource: the trx amount(in base units) that is delegated to others group by resource type
- withdrawableUnstaked: the trx amount(in base units) that is unstaked and can be withdraw
""",
                    "parameters": GetStakeInfoParameters,
                },
                lambda _params: self.get_stake_info(),
            ),
            create_tool(
                {
                    "name": "get_delegated_resource",
                    "description": "Get the info of resource delegated from `from_address` to `to_address`",
                    "parameters": GetDelegatedResourceParameters,
                },
                self.get_delegated_resource,
            ),
        ]

        sending_tron_tools = []
        if self.enable_send:
            sending_tron_tools = [
                create_tool(
                    {
                        "name": "send_token",
                        "description": "Send native currency or a TRC20 token to a recipient.",
                        "parameters": SendTokenParameters,
                    },
                    self.send_token,
                ),
                create_tool(
                    {
                        "name": "approve_token_tron",
                        "description": "Approve an amount of a TRC20 token for a spender.",
                        "parameters": ApproveParameters,
                    },
                    self.approve,
                ),
                create_tool(
                    {
                        "name": "revoke_token_approval_tron",
                        "description": "Revoke approval for a TRC20 token from a spender.",
                        "parameters": RevokeApprovalParameters,
                    },
                    self.revoke_approval,
                ),
                create_tool(
                    {
                        "name": "freeze_balance",
                        "description": "Freeze TRX to obtain ENERGY or BANDWIDTH (Stake 2.0). Amount is in SUN.",
                        "parameters": FreezeBalanceParameters,
                    },
                    self.freeze_balance,
                ),
                create_tool(
                    {
                        "name": "unfreeze_balance",
                        "description": "Unstake TRX (Stake 2.0). Optional amount in SUN; omitting unfreezes all for the resource.",
                        "parameters": UnfreezeBalanceParameters,
                    },
                    self.unfreeze_balance,
                ),
                create_tool(
                    {
                        "name": "withdraw_stake_balance",
                        "description": "Withdraw expired unstaked TRX after cool-down period (Stake 2.0).",
                        "parameters": WithdrawStakeBalanceParameters,
                    },
                    self.withdraw_stake_balance,
                ),
                create_tool(
                    {
                        "name": "delegate_resource",
                        "description": "Delegate ENERGY/BANDWIDTH to another address (Stake 2.0). Amount in SUN.",
                        "parameters": DelegateResourceParameters,
                    },
                    self.delegate_resource,
                ),
                create_tool(
                    {
                        "name": "undelegate_resource",
                        "description": "Cancel delegation of ENERGY/BANDWIDTH to another address (Stake 2.0). Amount in SUN.",
                        "parameters": UndelegateResourceParameters,
                    },
                    self.undelegate_resource,
                ),
                create_tool(
                    {
                        "name": "vote_witness",
                        "description": "Vote for witnesses. Provide a list of {witnessAddress, voteCount}.",
                        "parameters": VoteWitnessParameters,
                    },
                    self.vote_witness,
                ),
                create_tool(
                    {
                        "name": "withdraw_rewards",
                        "description": "Withdraw voting rewards.",
                        "parameters": WithdrawRewardsParameters,
                    },
                    self.withdraw_rewards,
                ),
            ]

        return base_tools + common_tron_tools + sending_tron_tools
