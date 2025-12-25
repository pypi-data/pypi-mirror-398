import inspect
import os
from collections.abc import Callable
from typing import Annotated, Any

from sun_agent_toolkit.core import WalletClientBase
from sun_agent_toolkit.core.classes.tool_base import ToolBase
from sun_agent_toolkit.core.utils.get_tools import get_plugin_tools, get_wallet_tools


class LLMConfig:
    """LLM 配置管理器（Azure OpenAI）
    从环境变量读取 Azure OpenAI 所需配置。
    """

    @staticmethod
    def from_env() -> dict[str, Any]:
        """从环境变量创建 Azure OpenAI 配置"""
        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "azure_deployment": os.getenv("OPENAI_DEPLOYMENT"),
            "api_version": os.getenv("OPENAI_API_VERSION", "2024-02-01"),
            "azure_endpoint": os.getenv("OPENAI_ENDPOINT"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }


class ToolWrapper:
    """工具包装器，用于新版 autogen"""

    def __init__(self, name: str, description: str, func: Callable[..., Any]):
        self.name = name
        self.description = description
        self.func_or_tool = func


def build_typed_tool(raw_tool: ToolBase[Any]) -> ToolWrapper | None:
    """将 ToolBase 实例转换为带参数注解的可调用工具函数，并包装为 ToolWrapper。

    返回：
        ToolWrapper 或 None（当 raw_tool 无可用参数模型时）
    """
    # 必须具备 Pydantic 参数模型
    if not hasattr(raw_tool, "parameters") or not raw_tool.parameters:
        return None

    parameters_model = raw_tool.parameters

    # 从 Pydantic 模型生成字段信息
    schema = parameters_model.model_json_schema()
    properties = schema.get("properties", {})

    # 构建参数注解（Annotated[type, description]）
    param_annotations: dict[str, Any] = {}
    for field_name, field_info in properties.items():
        field_type = parameters_model.__annotations__.get(field_name, Any)
        description = field_info.get("description", "")
        param_annotations[field_name] = Annotated[field_type, description]

    def make_annotated_tool_function(t: ToolBase[Any], annotations: dict[str, Any]) -> ToolWrapper:
        # 生成动态函数签名
        param_names = list(annotations.keys())
        parameters: list[inspect.Parameter] = []
        for name in param_names:
            param = inspect.Parameter(
                name=name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=annotations[name]
            )
            parameters.append(param)

        new_sig = inspect.Signature(parameters=parameters, return_annotation=Any)

        async def tool_function(*args: Any, **kwargs: Any) -> Any:
            bound_args = new_sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_params = dict(bound_args.arguments)
            return await t.execute(all_params)

        # 写操作确认由上层处理

        # 应用动态签名与元数据
        tool_function.__signature__ = new_sig  # type: ignore
        tool_function.__annotations__ = dict(annotations)
        tool_function.__annotations__["return"] = Any
        tool_function.__name__ = t.name
        tool_function.__qualname__ = t.name
        tool_function.__doc__ = t.description

        # 追加详细参数文档
        param_docs: list[str] = []
        for name, annot in annotations.items():
            if hasattr(annot, "__origin__") and annot.__origin__ is Annotated:
                _, desc = annot.__args__
                typ = annot.__args__[0]
                type_name = typ.__name__ if hasattr(typ, "__name__") else str(typ)
                param_docs.append(f"{name} ({type_name}): {desc}")

        docstring = f"{t.description}\n\nParameters:\n" + "\n".join(f"    {d}" for d in param_docs)
        docstring += "\n\nReturns:\n    The result of the tool execution"
        tool_function.__doc__ = docstring

        return ToolWrapper(name=t.name, description=t.description, func=tool_function)

    return make_annotated_tool_function(raw_tool, param_annotations)


def get_on_chain_wallet_tools(wallet: WalletClientBase) -> list[ToolWrapper]:
    """仅返回钱包核心工具的类型化包装版本。"""
    typed_functions: list[ToolWrapper] = []
    raw_tools = get_wallet_tools(wallet)
    for raw_tool in raw_tools:
        wrapped = build_typed_tool(raw_tool)
        if wrapped is not None:
            typed_functions.append(wrapped)
    return typed_functions


def get_on_chain_plugin_tools(wallet: WalletClientBase, plugins: list[Any]) -> list[ToolWrapper]:
    """仅返回插件工具的类型化包装版本。"""
    typed_functions: list[ToolWrapper] = []
    raw_tools = get_plugin_tools(wallet, plugins)
    for raw_tool in raw_tools:
        wrapped = build_typed_tool(raw_tool)
        if wrapped is not None:
            typed_functions.append(wrapped)
    return typed_functions


def get_on_chain_single_plugin_tools(wallet: WalletClientBase, plugin: Any) -> list[ToolWrapper]:
    """仅返回单个插件工具的类型化包装版本。"""
    typed_functions: list[ToolWrapper] = []
    from sun_agent_toolkit.core.utils.get_tools import get_plugin_tools

    raw_tools = get_plugin_tools(wallet, [plugin])
    for raw_tool in raw_tools:
        wrapped = build_typed_tool(raw_tool)
        if wrapped is not None:
            typed_functions.append(wrapped)
    return typed_functions
