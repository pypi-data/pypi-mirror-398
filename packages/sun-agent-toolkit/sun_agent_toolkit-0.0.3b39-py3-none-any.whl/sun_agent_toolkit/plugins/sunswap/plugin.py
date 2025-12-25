from dataclasses import dataclass
from typing import cast

from sun_agent_toolkit.core.classes.plugin_base import PluginBase
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.types.chain import Chain

from .service import SunSwapService


@dataclass
class SunSwapPluginOptions:
    # 预留扩展位，例如默认 Router 地址等（此处先不强制）
    default_router: str | None = None


class SunSwapPlugin(PluginBase[WalletClientBase]):
    def __init__(self, options: SunSwapPluginOptions | None = None):
        if options is None:
            options = SunSwapPluginOptions()
        # 构建工具提供者并上行转型为 list[object] 以满足基类签名
        providers = cast(list[object], [SunSwapService()])
        super().__init__("sunswap", providers)

    def supports_chain(self, chain: Chain) -> bool:
        chain_type = chain.get("type")
        if chain_type == "tron":
            return True
        chain_id = chain.get("id")
        return isinstance(chain_id, str) and chain_id.startswith("tron")


def sunswap(options: SunSwapPluginOptions | None = None) -> SunSwapPlugin:
    return SunSwapPlugin(options)
