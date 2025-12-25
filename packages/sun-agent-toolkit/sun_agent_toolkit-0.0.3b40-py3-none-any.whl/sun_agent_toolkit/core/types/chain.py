from typing import Literal, TypedDict


class NativeCurrency(TypedDict):
    """Native currency type definition

    Args:
        name: Currency name
        symbol: Currency symbol
        decimals: Number of decimals
    """

    name: str
    symbol: str
    decimals: int


class EvmChain(TypedDict):
    """EVM chain type definition

    Args:
        type: Literal "evm" chain type identifier
        id: Chain ID number for EVM networks
        nativeCurrency: Native currency information
    """

    type: Literal["evm"]
    id: int
    nativeCurrency: NativeCurrency


class SolanaChain(TypedDict):
    """Solana chain type definition

    Args:
        type: Literal "solana" chain type identifier
        nativeCurrency: Native currency information
    """

    type: Literal["solana"]
    nativeCurrency: NativeCurrency


class AptosChain(TypedDict):
    """Aptos chain type definition

    Args:
        type: Literal "aptos" chain type identifier
    """

    type: Literal["aptos"]


class ChromiaChain(TypedDict):
    """Chromia chain type definition

    Args:
        type: Literal "chromia" chain type identifier
    """

    type: Literal["chromia"]


class MultiversXChain(TypedDict):
    """MultiversX chain type definition

    Args:
        type: Literal "multiversx" chain type identifier
    """

    type: Literal["multiversx"]


class TronChain(dict[str, object]):
    """TRON chain type definition"""

    def __init__(self, network: str = "mainnet", name: str | None = None):
        """
        Initialize TRON chain

        Args:
            network: TRON network (mainnet, shasta, nile)
            name: Human readable name for the network
        """
        # TRON network configurations
        network_configs = {
            "mainnet": {
                "id": "tron-mainnet",
                "name": "TRON Mainnet",
                "rpc_url": "https://api.trongrid.io",
                "explorer": "https://tronscan.org",
            },
            "shasta": {
                "id": "tron-shasta",
                "name": "TRON Shasta Testnet",
                "rpc_url": "https://api.shasta.trongrid.io",
                "explorer": "https://shasta.tronscan.org",
            },
            "nile": {
                "id": "tron-nile",
                "name": "TRON Nile Testnet",
                "rpc_url": "https://nile.trongrid.io",
                "explorer": "https://nile.tronscan.org",
            },
        }

        if network not in network_configs:
            raise ValueError(f"Unsupported TRON network: {network}. Supported: {list(network_configs.keys())}")

        config = network_configs[network]
        super().__init__(
            type="tron",
            network=network,
            id=config["id"],
            name=name or config["name"],
            rpc_url=config["rpc_url"],
            explorer=config["explorer"],
        )


Chain = EvmChain | TronChain | SolanaChain | AptosChain | ChromiaChain | MultiversXChain
