import asyncio
import functools
import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import (
    Any,
    Generic,
    TypedDict,
    TypeVar,
)

from pydantic import BaseModel

TResult = TypeVar("TResult")


class ToolConfig(TypedDict):
    """
    Configuration interface for creating a Tool

    Generic Parameters:
        TResult: The return type of the tool's execution

    Attributes:
        name: The name of the tool
        description: A description of what the tool does
        parameters: The Pydantic model class defining the tool's parameters
    """

    name: str
    description: str
    parameters: type[BaseModel]


class ToolBase(Generic[TResult], ABC):
    """
    Abstract base class for creating tools with typed results

    Generic Parameters:
        TResult: The return type of the tool's execution

    Attributes:
        name: The name of the tool
        description: A description of what the tool does
        parameters: The Pydantic model class defining the tool's parameters
    """

    name: str
    description: str
    parameters: type[BaseModel]

    def __init__(self, config: ToolConfig):
        """
        Creates a new Tool instance

        Args:
            config: The configuration object for the tool containing name, description, and parameter model
        """
        super().__init__()
        self.name = config["name"]
        self.description = config["description"]
        self.parameters = config["parameters"]

    @abstractmethod
    async def execute(self, parameters: dict[str, Any]) -> TResult:
        """
        Executes the tool with the provided parameters

        Args:
            parameters: The parameters for the tool execution, validated against the tool's Pydantic model

        Returns:
            The result of the tool execution
        """
        pass


def create_tool(config: ToolConfig, execute_fn: Callable[[dict[str, Any]], Any]) -> ToolBase[Any]:
    """
    Creates a new Tool instance with the provided configuration and execution function

    Args:
        config: The configuration object for the tool containing name, description, and parameter model
        execute_fn: The function to be called when the tool is executed

    Returns:
        A new Tool instance that validates parameters using the provided Pydantic model
    """

    class Tool(ToolBase[Any]):
        async def execute(self, parameters: dict[str, Any]) -> Any:
            # 1. 参数验证
            validated_params = self.parameters.model_validate(parameters)
            params_dump = validated_params.model_dump()

            # 2. 判断 execute_fn 是同步还是异步
            if inspect.iscoroutinefunction(execute_fn):
                # --- 处理异步函数 ---
                return await execute_fn(params_dump)
            else:
                # --- 处理同步函数 ---
                # 如果 execute_fn 是一个普通的、可能会阻塞的同步函数，
                # 将其放入一个单独的线程中运行。
                loop = asyncio.get_running_loop()

                result = await loop.run_in_executor(None, functools.partial(execute_fn, params_dump))
                return result

    return Tool(config)
