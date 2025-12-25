import logging
from collections.abc import Callable
from typing import Any

from autogen_core.tools import FunctionTool

from sun_agent_toolkit.core import WalletClientBase

from .utils import get_on_chain_plugin_tools, get_on_chain_wallet_tools


def get_on_chain_tools(wallet: WalletClientBase, plugins: list[Any]) -> list[FunctionTool]:
    """Create autogen tools from SAT tools.

    Args:
        wallet: A wallet client instance
        plugins: List of plugin instances

    Returns:
        List of autogen Tool instances configured with the SAT tools
    """
    tools = get_on_chain_wallet_tools(wallet) + get_on_chain_plugin_tools(wallet, plugins)
    autogen_tools: list[FunctionTool] = []
    for t in tools:
        if hasattr(t, "func_or_tool"):
            try:
                tool = FunctionTool(t.func_or_tool, description=t.description)
                autogen_tools.append(tool)
            except Exception as e:
                logging.warning(f"跳过工具 {getattr(tool, 'name', 'unknown')}: {str(e)}")
                continue

    return autogen_tools


def get_on_chain_callable(wallet: WalletClientBase, plugins: list[Any], function_name: str) -> Callable[..., Any]:
    """根据函数名获取可直接调用的工具函数。

    Args:
        wallet: 钱包客户端实例
        plugins: 插件实例列表
        function_name: 工具名称或底层函数名称

    Returns:
        可直接调用的工具函数（异步）

    Raises:
        KeyError: 当找不到对应名称的工具函数时
    """
    tools = get_on_chain_wallet_tools(wallet) + get_on_chain_plugin_tools(wallet, plugins)
    for tool in tools:
        func = getattr(tool, "func_or_tool", None)
        if func is None:
            continue

        candidate_names: set[str | None] = {getattr(tool, "name", None)}
        func_name = getattr(func, "__name__", None)
        if func_name:
            candidate_names.add(func_name)

        if function_name in candidate_names:
            return func

    raise KeyError(f"未找到名称为 {function_name!r} 的链上工具函数")
