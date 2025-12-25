from __future__ import annotations

import os
from dataclasses import dataclass

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .env import DEFAULT_ENV
from .service import SunIOService


@dataclass
class SunIOPluginOptions:
    """Options for the SunIOPlugin."""

    base_url: str  # Base URL for SunIO API
    api_key: str | None = None  # API key for external service integration

    @classmethod
    def default_options(cls, network: str) -> SunIOPluginOptions:
        defaults = DEFAULT_ENV.get(network)
        if defaults is None:
            raise ValueError(f"sunio network {network} is not supported")
        return cls(base_url=defaults.get("base_url", ""))

    @classmethod
    def from_env(cls) -> SunIOPluginOptions:
        network = os.getenv("TRON_NETWORK")
        if not network:
            raise ValueError("请指定环境变量 'TRON_NETWORK'")
        options = cls.default_options(network=network)
        options.api_key = os.getenv("SUNIO_OPENAPI_KEY")
        return options


class SunIOPlugin(PluginBase[WalletClientBase]):
    """SunIO plugin for token swaps on supported EVM chains."""

    def __init__(self, options: SunIOPluginOptions):
        super().__init__("sunio", [SunIOService(options.base_url, options.api_key)])

    def supports_chain(self, chain: Chain) -> bool:
        """Check if the chain is supported by SunIO."""

        chain_type = chain.get("type")
        if chain_type == "tron":
            return True
        chain_id = chain.get("id")
        return isinstance(chain_id, str) and chain_id.startswith("tron")


def sunio(options: SunIOPluginOptions) -> SunIOPlugin:
    """Create a new instance of the SunIO plugin.

    Args:
        options: Configuration options for the plugin

    Returns:
        A configured SunIOPlugin instance
    """
    return SunIOPlugin(options)
