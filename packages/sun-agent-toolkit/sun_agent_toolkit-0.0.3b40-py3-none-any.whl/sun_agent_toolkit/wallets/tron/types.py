from typing import Any, TypedDict

from typing_extensions import NotRequired


class TronTriggerSmartContractOptions(TypedDict):
    """Options for triggering smart contract calls on TRON"""

    fee_limit: NotRequired[int]  # Maximum fee in SUN
    call_value: NotRequired[int]  # TRX amount to send in SUN


class TronTransactionOptions(TypedDict):
    """Options for TRON transactions"""

    trigger_smart_contract: NotRequired[TronTriggerSmartContractOptions]


class TronTransaction(TypedDict):
    """TRON transaction structure"""

    to: str  # Recipient address
    functionName: NotRequired[str]  # Smart contract function name
    args: NotRequired[list[Any]]  # Function arguments
    value: NotRequired[int]  # TRX amount in SUN
    abi: NotRequired[list[dict[str, Any]]]  # Contract ABI
    options: NotRequired[TronTransactionOptions]
    data: NotRequired[str]  # Raw transaction data
    feeLimit: NotRequired[int]  # Maximum fee limit in SUN


class TronReadRequest(TypedDict):
    """TRON smart contract read request"""

    address: str  # Contract address
    functionName: str  # Function to call
    args: NotRequired[list[Any]]  # Function arguments
    abi: list[dict[str, Any]]  # Contract ABI


class TronReadResult(TypedDict):
    """Result from TRON smart contract read"""

    value: Any  # Returned value
