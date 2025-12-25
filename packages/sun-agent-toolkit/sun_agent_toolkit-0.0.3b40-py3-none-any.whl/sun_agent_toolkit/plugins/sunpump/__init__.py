from __future__ import annotations

import os
from dataclasses import dataclass

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .env import DEFAULT_ENV
from .service import SunPumpService


@dataclass
class SunPumpPluginOptions:
    """Options for the SunPumpPlugin."""

    base_url: str  # Base URL for SunPump API
    openapi_base_url: str  # Base URL for SunPump Open API
    pump_contract: str
    private_key: str | None = None

    @classmethod
    def default_options(cls, network: str) -> SunPumpPluginOptions:
        defaults = DEFAULT_ENV.get(network)
        if defaults is None:
            raise ValueError(f"sunpump network {network} is not supported")
        return cls(
            base_url=defaults.get("base_url", ""),
            openapi_base_url=defaults.get("openapi_base_url", ""),
            pump_contract=defaults.get("pump_contract", ""),
        )

    @classmethod
    def from_env(cls) -> SunPumpPluginOptions:
        network = os.getenv("TRON_NETWORK")
        if not network:
            raise ValueError("请指定环境变量 'TRON_NETWORK'")
        options = cls.default_options(network)
        options.private_key = os.getenv("SUNPUMP_OPENAPI_PRIVATE_KEY")
        return options


class SunPumpPlugin(PluginBase[WalletClientBase]):
    """SunPump plugin for token swaps on supported EVM chains."""

    def __init__(self, options: SunPumpPluginOptions):
        super().__init__(
            "sunpump",
            [
                SunPumpService(
                    options.base_url,
                    options.openapi_base_url,
                    options.pump_contract,
                    options.private_key,
                )
            ],
        )

    def supports_chain(self, chain: Chain) -> bool:
        """Check if the chain is supported by SunPump."""

        chain_type = chain.get("type")
        if chain_type == "tron":
            return True
        chain_id = chain.get("id")
        return isinstance(chain_id, str) and chain_id.startswith("tron")


def sunpump(options: SunPumpPluginOptions) -> SunPumpPlugin:
    """Create a new instance of the SunPump plugin.

    Args:
        options: Configuration options for the plugin

    Returns:
        A configured SunPumpPlugin instance
    """
    return SunPumpPlugin(options)
