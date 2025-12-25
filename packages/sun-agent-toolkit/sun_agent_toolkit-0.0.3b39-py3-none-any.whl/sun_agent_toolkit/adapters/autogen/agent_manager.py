import json
import logging
import os
from typing import Any, Literal

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from pydantic import BaseModel

from sun_agent_toolkit.core import PluginBase, WalletClientBase
from sun_agent_toolkit.plugins.sunio import SunIOPluginOptions, sunio
from sun_agent_toolkit.plugins.sunpump import SunPumpPluginOptions, sunpump
from sun_agent_toolkit.plugins.tronscan import TronScanPluginOptions, tronscan
from sun_agent_toolkit.wallets.tron import TronWalletClient

from .utils import LLMConfig, get_on_chain_plugin_tools, get_on_chain_wallet_tools


# 定义结构化输出格式
class TronAgentResponse(BaseModel):
    """TRON Agent 的结构化响应格式"""

    result_type: Literal["requires_approval", "requires_info", "completed", "error"]
    thoughts: str  # Agent 的思考过程
    message: str  # 具体的消息内容
    error: str | None = None  # 执行异常信息


class AutogenAgentFactory:
    @staticmethod
    def create_agent(
        wallet: WalletClientBase, llm_config: dict[str, Any] | None = None, agent_name: str = "tron_assistant"
    ) -> AssistantAgent:
        # 使用默认配置（从 utils.LLMConfig 读取）
        config = llm_config or LLMConfig.from_env()
        plugins = [
            tronscan(TronScanPluginOptions.from_env()),
            sunio(SunIOPluginOptions.from_env()),
            sunpump(SunPumpPluginOptions.from_env()),
        ]

        # 创建模型客户端
        model_client = AzureOpenAIChatCompletionClient(
            model=str(config.get("model", "")),
            azure_deployment=str(config.get("azure_deployment", "")),
            api_version=str(config.get("api_version", "2024-02-01")),
            azure_endpoint=str(config.get("azure_endpoint", "")),
            api_key=str(config.get("api_key", "")),
        )

        # 获取工具
        tools = AutogenAgentFactory._get_tools(wallet, plugins)

        # 生成系统提示
        system_prompt = AutogenAgentFactory._build_system_prompt(wallet, plugins)

        # 创建并返回 AssistantAgent（不使用 output_content_type，由提示词约束 JSON 输出）
        return AssistantAgent(
            name=agent_name,
            model_client=model_client,
            tools=tools,
            system_message=system_prompt,
            reflect_on_tool_use=False,
            max_tool_iterations=10,
        )

    @staticmethod
    def _get_tools(wallet: WalletClientBase, plugins: list[Any]) -> list[Any]:
        """获取工具函数列表，为结构化输出配置工具"""
        from autogen_core.tools import FunctionTool

        wallet_tools = get_on_chain_wallet_tools(wallet)
        plugin_tools = get_on_chain_plugin_tools(wallet, plugins)
        all_tools = wallet_tools + plugin_tools

        # 将工具包装为 FunctionTool，暂时禁用 strict 模式避免 schema 问题
        function_tools: list[Any] = []
        for tool in all_tools:
            if hasattr(tool, "func_or_tool"):
                try:
                    function_tool = FunctionTool(tool.func_or_tool, description=tool.description, strict=False)
                    function_tools.append(function_tool)
                except Exception as e:
                    # 如果工具创建失败，记录错误但继续处理其他工具
                    logging.warning(f"跳过工具 {getattr(tool, 'name', 'unknown')}: {str(e)}")
                    continue

        return function_tools

    @staticmethod
    def _build_system_prompt(wallet: WalletClientBase, plugins: list[PluginBase[WalletClientBase]]) -> str:
        # 分别获取钱包工具和插件工具

        wallet_tools = get_on_chain_wallet_tools(wallet)
        plugin_tools = get_on_chain_plugin_tools(wallet, plugins)

        # 构建钱包工具描述
        wallet_tool_names: list[str] = []
        for tool in wallet_tools:
            if hasattr(tool, "name"):
                wallet_tool_names.append(tool.name)
            elif hasattr(tool.func_or_tool, "__name__"):
                wallet_tool_names.append(tool.func_or_tool.__name__)

        # 构建插件工具描述
        plugin_tool_names: list[str] = []
        for tool in plugin_tools:
            if hasattr(tool, "name"):
                plugin_tool_names.append(tool.name)
            elif hasattr(tool.func_or_tool, "__name__"):
                plugin_tool_names.append(tool.func_or_tool.__name__)

        # 生成工具描述
        wallet_description = (
            f"Wallet tools: {', '.join(wallet_tool_names)}" if wallet_tool_names else "Wallet tools: None"
        )
        plugin_description = (
            f"Plugin tools: {', '.join(plugin_tool_names)}" if plugin_tool_names else "Plugin tools: None"
        )

        tools_description = f"{wallet_description}\n{plugin_description}"

        role_description = (
            "You are a TRON blockchain agent handling various blockchain operations. " "Respond in Chinese by default."
        )
        safety_note = "Ensure data query accuracy and completeness."

        system_prompt = f"""{role_description}

{tools_description}

**EXECUTION WORKFLOW:**
1. **Analyze Task**: Understand user request, identify task type and required steps
2. **Create Plan**: Develop detailed execution plan based on task requirements
3. **Execute Stepwise**: Execute each step in planned sequence
4. **Information Gathering**: Stop immediately and request user input if missing necessary information
5. **Confirm Write Operations**: For any write/modify operations, obtain explicit user confirmation before execution
6. **Complete Feedback**: Provide clear execution results and status updates

**HANDLING PRINCIPLES:**
- Query operations: Execute automatically, provide complete results
- Write operations: Explain intended actions first, wait for user confirmation
- Missing information: Clearly state what information is needed, pause execution
- Multi-step tasks: Execute progressively, report progress after each step
- Error handling: Explain causes and suggest solutions when errors occur

**CRITICAL PARAMETER RULES:**
- NEVER fabricate, guess, or make up parameter values (especially addresses, tokens, IDs)
- If a function requires parameters not provided by the user, ASK the user for them explicitly
- Do NOT assume default values for addresses, token contracts, or identifiers
- When querying balances, only use null/None for optional token parameters if user wants native TRX balance
- For specific token balances, ALWAYS ask user to provide the exact token contract address

**RESPONSE FORMAT (STRICT JSON):**
You MUST output exactly one valid JSON object in a single line with the following fields:
- result_type: one of ["requires_approval", "requires_info", "completed", "error"]
- thoughts: string
- message: string
- error: string or null (omit or set to null if no error)

Requirements:
- Output ONLY the JSON. No markdown, no code fences, no extra text.
- Keys must match exactly. Do not include additional fields.
- Keep it as a single JSON object, not an array.

**RESULT TYPE GUIDELINES:**
- Use "requires_approval" for any write/modify operations (transfers, contract calls, etc.)
- Use "requires_info" when requesting missing information or asking for additional parameters
- Use "completed" when tasks are successfully finished
- Use "error" when execution fails due to exceptions or errors

{safety_note}"""

        return system_prompt

    @staticmethod
    def _get_wallet_address(wallet: WalletClientBase) -> str | None:
        """获取钱包地址"""
        if not wallet:
            return None

        try:
            if hasattr(wallet, "get_address"):
                return wallet.get_address()
            else:
                addr = getattr(wallet, "address", None)
                if isinstance(addr, str):
                    return addr
        except Exception as e:
            logging.debug("获取钱包地址失败: %s", e)

        return None


class AutoGenAgentManager:
    def __init__(
        self,
        wallet: WalletClientBase | None = None,
        llm_config: dict[str, Any] | None = None,
    ):
        # 若未提供 wallet，则从环境创建 TronWalletClient
        if wallet is None:
            pk = os.getenv("TRON_PRIVATE_KEY")
            if not pk:
                raise RuntimeError("Missing TRON_PRIVATE_KEY in environment variables")
            net = os.getenv("TRON_NETWORK", "shasta")
            wallet = TronWalletClient(private_key=pk, network=net)

        # 若未提供 llm_config，则从环境加载
        llm_config = llm_config or LLMConfig.from_env()

        # 使用工厂方法创建代理
        self.agent = AutogenAgentFactory.create_agent(wallet, llm_config)
        self.conversation_history: list[dict[str, Any]] = []

    async def ask(self, message: str) -> TronAgentResponse:
        self.conversation_history.append({"role": "user", "content": message})

        from autogen_agentchat.base import TaskResult
        from autogen_agentchat.messages import TextMessage

        # 创建消息对象
        text_message = TextMessage(content=message, source="user")

        # 使用 Console 包裹流式运行
        from autogen_agentchat.ui import Console

        result = await Console(self.agent.run_stream(task=text_message))

        response_content = None
        if isinstance(result, TaskResult) and result.messages:
            last_message = result.messages[-1]
            response_content = getattr(last_message, "content", None)

        # 将代理文本结果解析为 TronAgentResponse（JSON -> Pydantic）
        content_text = None
        if response_content is not None:
            content_text = str(response_content)
        else:
            content_text = str(result)

        def _parse_json_to_response(text: str) -> TronAgentResponse | None:
            # 尝试直接解析
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return TronAgentResponse.model_validate(data)
            except Exception as e:
                logging.debug("直接解析 JSON 失败: %s", e)
            # 若包含代码块或前后多余文本，尝试提取首尾花括号内容
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    snippet = text[start : end + 1]
                    data = json.loads(snippet)
                    if isinstance(data, dict):
                        return TronAgentResponse.model_validate(data)
            except Exception as e:
                logging.debug("从文本片段解析 JSON 失败: %s", e)
            return None

        parsed = _parse_json_to_response(content_text)
        if parsed is not None:
            sr = parsed
        else:
            # 解析失败时，作为普通文本返回 completed，避免中断流程
            sr = TronAgentResponse(result_type="completed", thoughts="", message=content_text)

        self.conversation_history.append({"role": "assistant", "content": sr.model_dump()})
        return sr

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history.copy()
