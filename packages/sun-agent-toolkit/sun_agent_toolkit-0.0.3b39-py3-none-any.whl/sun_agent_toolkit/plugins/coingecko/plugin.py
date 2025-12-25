from dataclasses import dataclass

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .service import CoinGeckoService


@dataclass
class CoinGeckoPluginOptions:
    api_key: str


class CoinGeckoPlugin(PluginBase[WalletClientBase]):
    def __init__(self, options: CoinGeckoPluginOptions):
        if not options or not options.api_key:
            raise ValueError("CoinGeckoPluginOptions.api_key is required")
        super().__init__("coingecko", [CoinGeckoService(options.api_key)])

    def supports_chain(self, chain: Chain) -> bool:
        # CoinGecko 与具体链无强依赖，这里统一返回 True
        return True


def coingecko(options: CoinGeckoPluginOptions) -> "CoinGeckoPlugin":
    return CoinGeckoPlugin(options)
