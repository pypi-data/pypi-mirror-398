import logging
from typing import Any, cast

from ..classes.plugin_base import PluginBase
from ..classes.tool_base import ToolBase
from ..classes.wallet_client_base import WalletClientBase
from ..types.chain import Chain

logger = logging.getLogger(__name__)


def get_wallet_tools(wallet: WalletClientBase) -> list[ToolBase[Any]]:
    """获取钱包自身提供的核心工具列表。"""
    # wallet.get_core_tools() 返回 list[ToolBase[Any]]
    return list(wallet.get_core_tools())


def get_plugin_tools(
    wallet: WalletClientBase, plugins: list[PluginBase[WalletClientBase]] | None = None
) -> list[ToolBase[Any]]:
    """从插件中获取与当前链兼容的工具列表。会自动跳过不兼容插件。"""
    tools: list[ToolBase[Any]] = []
    plugins = plugins or []

    chain: Chain = wallet.get_chain()
    chain_dict = cast(dict[str, Any], chain)
    for plugin in plugins:
        if not plugin.supports_chain(chain):
            chain_id = f" chain id {chain_dict.get('id')}" if "id" in chain_dict else ""
            type_name = cast(str, chain_dict.get("type", "unknown"))
            logger.warning(
                "Plugin %s does not support %s%s. Skipping.",
                plugin.name,
                type_name,
                chain_id,
            )
            continue

        plugin_tools = plugin.get_tools(wallet)
        tools.extend(plugin_tools)

    return tools


def get_tools(
    wallet: WalletClientBase, plugins: list[PluginBase[WalletClientBase]] | None = None
) -> list[ToolBase[Any]]:
    """Get all tools from the wallet and plugins."""
    core_tools = get_wallet_tools(wallet)
    plugin_tools = get_plugin_tools(wallet, plugins)
    return [*core_tools, *plugin_tools]
