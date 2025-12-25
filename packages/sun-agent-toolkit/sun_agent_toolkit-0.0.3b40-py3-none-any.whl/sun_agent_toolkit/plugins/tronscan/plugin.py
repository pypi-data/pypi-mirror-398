from __future__ import annotations

import os
from dataclasses import dataclass

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .env import DEFAULT_ENV
from .service import TronScanService


@dataclass
class TronScanPluginOptions:
    base_url: str
    api_key: str | None = None

    @classmethod
    def default_options(cls, network: str) -> TronScanPluginOptions:
        defaults = DEFAULT_ENV.get(network)

        if defaults is None:
            raise ValueError(f"tronscan network {network} is not supported")
        return cls(
            base_url=defaults.get("base_url", ""),
        )

        api_key = os.getenv("TRONSCAN_API_KEY")
        require_key = "apilist.tronscanapi.com" in options.base_url
        if require_key and not api_key:
            raise ValueError("请配置环境变量 'TRONSCAN_API_KEY' 以访问主网 TronScan API")
        options.api_key = api_key
        return options

    @classmethod
    def from_env(cls) -> TronScanPluginOptions:
        network = os.getenv("TRON_NETWORK")
        if not network:
            raise ValueError("请指定环境变量 'TRON_NETWORK'")
        options = cls.default_options(network)
        api_key = os.getenv("TRONSCAN_API_KEY")
        require_key = "apilist.tronscanapi.com" in options.base_url
        if require_key and not api_key:
            raise ValueError("请配置环境变量 'TRONSCAN_API_KEY' 以访问主网 TronScan API")
        options.api_key = api_key
        return options


class TronScanPlugin(PluginBase[WalletClientBase]):
    def __init__(self, options: TronScanPluginOptions):
        super().__init__("tronscan", [TronScanService(options.base_url, options.api_key)])

    def supports_chain(self, chain: Chain) -> bool:
        chain_type = chain.get("type")
        if chain_type == "tron":
            return True
        chain_id = chain.get("id")
        return isinstance(chain_id, str) and chain_id.startswith("tron")


def tronscan(options: TronScanPluginOptions) -> TronScanPlugin:
    return TronScanPlugin(options)
