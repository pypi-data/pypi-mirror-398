import asyncio
import functools
import inspect
import threading
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import Any, Generic, TypeVar

from sun_agent_toolkit.core.classes.tool_base import ToolBase, create_tool
from sun_agent_toolkit.core.classes.wallet_client_base import WalletClientBase
from sun_agent_toolkit.core.decorators.tool import TOOL_METADATA_KEY, StoredToolMetadata
from sun_agent_toolkit.core.types.chain import Chain

TWalletClient = TypeVar("TWalletClient", bound=WalletClientBase)


class PluginBase(Generic[TWalletClient], ABC):
    """
    Abstract base class for plugins that provide tools for wallet interactions.
    """

    def __init__(self, name: str, tool_providers: list[object]):
        """
        Creates a new Plugin instance.

        Args:
            name: The name of the plugin
            tool_providers: Array of class instances that provide tools. Must be actual instances,
                          not classes themselves.
        """
        if not all(isinstance(provider, object) and not isinstance(provider, type) for provider in tool_providers):
            raise TypeError("All tool providers must be class instances, not classes themselves")

        self.name = name
        self.tool_providers = tool_providers

    @abstractmethod
    def supports_chain(self, chain: Chain) -> bool:
        """
        Checks if the plugin supports a specific blockchain.

        Args:
            chain: The blockchain to check support for

        Returns:
            True if the chain is supported, false otherwise
        """
        pass

    def get_tools(self, wallet_client: TWalletClient) -> list[ToolBase[Any]]:
        """
        Retrieves the tools provided by the plugin.

        Args:
            wallet_client: The wallet client to use for tool execution

        Returns:
            An array of tools
        """
        tools: list[ToolBase[Any]] = []

        for tool_provider in self.tool_providers:
            # Get all methods of the tool provider instance
            for attr_name in dir(tool_provider):
                attr = getattr(tool_provider, attr_name)
                # Check if the method has tool metadata
                tool_metadata = getattr(attr, TOOL_METADATA_KEY, None)

                if tool_metadata:
                    tools.append(
                        create_tool(
                            {
                                "name": tool_metadata.name,
                                "description": tool_metadata.description,
                                "parameters": tool_metadata.parameters["schema"],
                            },
                            functools.partial(self._execute_tool, tool_metadata, tool_provider, wallet_client),
                        )
                    )

        return tools

    async def _execute_tool(
        self,
        tool_metadata: StoredToolMetadata,
        tool_provider: Any,
        wallet_client: WalletClientBase,
        params: Any,
    ) -> Any:
        """
        Helper method to execute a tool with the correct arguments.

        Args:
            tool: The tool metadata
            tool_provider: The instance providing the tool
            wallet_client: The wallet client to use
            params: The parameters for the tool

        Returns:
            The result of the tool execution
        """

        def _run_coroutine_in_new_thread(coro: Coroutine[Any, Any, Any]) -> Any:
            """Run a coroutine in a new thread with its own event loop."""
            result: Any | None = None
            exception: BaseException | None = None

            def run_coro() -> None:
                nonlocal result, exception
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(coro)
                except Exception as e:
                    exception = e
                finally:
                    loop.close()

            thread = threading.Thread(target=run_coro)
            thread.start()
            thread.join()

            if exception:
                raise exception
            return result

        wallet_client_index = tool_metadata.wallet_client.get("index")
        parameters_index = tool_metadata.parameters.get("index")

        max_index = 0
        for idx in (wallet_client_index, parameters_index):
            if isinstance(idx, int) and idx > 0:
                max_index = max(max_index, idx)

        args: list[Any] = [None] * max_index

        if isinstance(wallet_client_index, int) and wallet_client_index > 0:
            args[wallet_client_index - 1] = wallet_client

        if isinstance(parameters_index, int) and parameters_index > 0:
            args[parameters_index - 1] = params

        method = getattr(tool_provider, tool_metadata.target.__name__)
        result = method(*args)

        if inspect.iscoroutine(result):
            return await result

        return result
