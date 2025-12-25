import json
import logging
import urllib.parse
import urllib.request
from decimal import Decimal
from itertools import groupby
from typing import Any, cast

from sun_agent_toolkit.core.decorators.tool import Tool
from sun_agent_toolkit.wallets.tron.abi import SUNSWAP_SMART_ROUTER_ABI
from sun_agent_toolkit.wallets.tron.tron_wallet_base import TronWalletBase
from sun_agent_toolkit.wallets.tron.types import TronTransaction

from .parameters import (
    PurchaseSunPumpTokenParameters,
    RouterParameters,
    SaleSunPumpTokenParameters,
    SwapTokensParameters,
)

logger = logging.getLogger(__name__)


class _CalcServiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        if not base_url:
            raise ValueError("SunSwap CalculationService base_url is required")
        self.base_url = base_url.rstrip("/")

    def _get_json(self, params: dict[str, Any]) -> dict[str, Any]:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base_url}?{query}" if query else self.base_url
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError as e:
                raise ValueError(f"CalculationService invalid JSON: {body}") from e
            if resp.status < 200 or resp.status >= 300:
                if isinstance(parsed, dict):
                    err = cast(dict[str, Any], parsed).get("errorCode")
                else:
                    err = parsed
                raise ValueError(f"CalculationService error {resp.status}: {err}")
            if not isinstance(parsed, dict):
                raise ValueError("Unexpected CalculationService response format (expected object)")
            return cast(dict[str, Any], parsed)

    def get_router(self, *, fromToken: str, toToken: str, amountIn: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "fromToken": fromToken,
            "toToken": toToken,
            "amountIn": amountIn,
        }
        return self._get_json(params)


def select_best_route(route_result: dict[str, Any]) -> dict[str, Any]:
    code = route_result.get("code")
    if code != 0:
        raise RuntimeError(f"get_route failed: {route_result.get('message')}")
    routes = cast(list[dict[str, Any]] | None, route_result.get("data")) or []
    if not routes:
        raise RuntimeError("no routes returned")

    # 直接返回第一个路由
    best: dict[str, Any] = routes[0]
    return best


class SunSwapService:
    def __init__(self) -> None:
        pass

    def _resolve_client(self, wallet_client: TronWalletBase) -> _CalcServiceClient:
        # 根据钱包网络选择固定网关
        network = wallet_client.get_network_id()
        # 固定映射：mainnet/nile 有网关，shasta 不支持
        if network == "mainnet":
            url = "https://rot.endjgfsv.link/swap/router"
        elif network == "nile":
            url = "https://tnrouter.endjgfsv.link/swap/router"
        else:
            raise ValueError(f"不支持的网络: {network}")

        return _CalcServiceClient(url)

    @Tool(
        {
            "description": "获取智能路由报价",
            "parameters_schema": RouterParameters,
        }
    )
    def get_route(self, params: dict[str, Any], wallet_client: TronWalletBase) -> dict[str, Any]:
        from_token = cast(str, params["fromToken"])
        to_token = cast(str, params["toToken"])
        # 入参 amountIn 为 human，这里统一转换为 base（sun）；原生判断已在钱包实现
        amount_in_human = cast(str, params["amountIn"])
        amount_in_base = wallet_client.convert_to_base_units(
            {
                "amount": amount_in_human,
                "tokenAddress": from_token,
            }
        )
        client = self._resolve_client(wallet_client)
        result = client.get_router(fromToken=from_token, toToken=to_token, amountIn=amount_in_base)
        return result

    @Tool(
        {
            "description": "智能代币交换（自动识别 SunPump token 状态）",
            "parameters_schema": SwapTokensParameters,
        }
    )
    async def swap_tokens(self, params: dict[str, Any], wallet_client: TronWalletBase) -> dict[str, Any]:
        """智能交换：自动检测 SunPump token 状态并选择正确的交易方式。"""
        from_token = cast(str, params["fromToken"])
        to_token = cast(str, params["toToken"])

        logger.info(
            "[swap_tokens] fromToken=%s, toToken=%s, amountIn=%s",
            from_token,
            to_token,
            params.get("amountIn"),
        )

        # 检查是否为 SunPump token（支持买入和卖出场景）
        trx_address = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"

        # 场景 1：TRX -> Token（买入）
        if from_token == trx_address:
            token_state = self._get_sunpump_token_state(wallet_client, to_token)
            logger.info("[swap_tokens] SunPump token_state=%s for %s (buy)", token_state, to_token)

            if token_state == 1:  # ONSALE - Bonding Curve 期
                logger.info("[swap_tokens] Using Bonding Curve purchase for token %s", to_token)
                return await self.purchase_sunpump_token(wallet_client, params)

        # 场景 2：Token -> TRX（卖出）
        elif to_token == trx_address:
            token_state = self._get_sunpump_token_state(wallet_client, from_token)
            logger.info("[swap_tokens] SunPump token_state=%s for %s (sell)", token_state, from_token)

            if token_state == 1:  # ONSALE - Bonding Curve 期
                logger.info("[swap_tokens] Using Bonding Curve sale for token %s", from_token)
                return await self.sale_sunpump_token(wallet_client, params)

        # 默认使用 DEX 交易
        logger.info("[swap_tokens] Using DEX swap for %s -> %s", from_token, to_token)
        return await self._swap_on_dex(params, wallet_client)

    @Tool(
        {
            "description": "计算代币兑换数额",
            "parameters_schema": SwapTokensParameters,
        }
    )
    async def calculate_swap_amount(self, params: dict[str, Any], wallet_client: TronWalletBase) -> dict[str, Any]:
        """计算代币兑换数额：自动检测 SunPump token 状态并返回预估兑换结果，不执行实际交易。"""
        from_token = cast(str, params["fromToken"])
        to_token = cast(str, params["toToken"])
        amount_in_human = cast(str, params["amountIn"])

        logger.info(
            "[calculate_swap_amount] fromToken=%s, toToken=%s, amountIn=%s",
            from_token,
            to_token,
            amount_in_human,
        )

        # 检查是否为 SunPump token（支持买入和卖出场景）
        trx_address = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"

        # 场景 1：TRX -> Token（买入）
        if from_token == trx_address:
            token_state = self._get_sunpump_token_state(wallet_client, to_token)
            logger.info("[calculate_swap_amount] SunPump token_state=%s for %s (buy)", token_state, to_token)

            if token_state == 1:  # ONSALE - Bonding Curve 期
                logger.info("[calculate_swap_amount] Calculating Bonding Curve purchase for token %s", to_token)
                return self._calculate_sunpump_purchase(wallet_client, params)

        # 场景 2：Token -> TRX（卖出）
        elif to_token == trx_address:
            token_state = self._get_sunpump_token_state(wallet_client, from_token)
            logger.info("[calculate_swap_amount] SunPump token_state=%s for %s (sell)", token_state, from_token)

            if token_state == 1:  # ONSALE - Bonding Curve 期
                logger.info("[calculate_swap_amount] Calculating Bonding Curve sale for token %s", from_token)
                return self._calculate_sunpump_sale(wallet_client, params)

        # 默认使用 DEX 计算
        logger.info("[calculate_swap_amount] Calculating DEX swap for %s -> %s", from_token, to_token)
        return self._calculate_dex_swap(params, wallet_client)

    async def _swap_on_dex(self, params: dict[str, Any], wallet_client: TronWalletBase) -> dict[str, Any]:
        """在 DEX 上执行标准交换。"""
        from_token = cast(str, params["fromToken"])
        to_token = cast(str, params["toToken"])
        amount_in_human = cast(str, params["amountIn"])
        slippage_tolerance = cast(float, params.get("slippageTolerance", 0.005))  # 默认 0.5%

        # 1. 获取路由信息
        route_result = self.get_route(
            {
                "fromToken": from_token,
                "toToken": to_token,
                "amountIn": amount_in_human,
            },
            wallet_client,
        )

        best_route = select_best_route(route_result)
        # 调试：打印最佳路由
        logger.info(
            "[SunSwapService] fromToken: %s, toToken: %s, amountIn: %s, best_route: %s",
            from_token,
            to_token,
            amount_in_human,
            best_route,
        )

        # 4. 获取智能路由合约地址
        network = wallet_client.get_network_id()
        if network == "mainnet":
            router_address = "TCFNp179Lg46D16zKoumd4Poa2WFFdtqYj"
        elif network == "nile":
            # 官网文档 https://docs.sun.io/DEVELOPERS/Swap/SmartRouter/Contract
            # router_address = "TDAQGC5Ekd683GjekSaLzCaeg7jGsGSmbh"
            router_address = "TB6xBCixqRPUSKiXb45ky1GhChFJ7qrfFj"
        else:
            raise ValueError(f"不支持的网络: {network}")

        # 5. 准备交易参数
        user_address = wallet_client.get_address()

        # 6. 将 best_route 转为合约调用参数（path/pool_version/version_len/fees/swap_data）
        contract_args = self._build_swap_contract_args(
            best_route=best_route,
            to_address=user_address,
            wallet_client=wallet_client,
            slippage_tolerance=slippage_tolerance,
        )

        from_token_symbol = best_route["symbols"][0]
        # 8. 检查并处理代币授权
        if from_token_symbol.lower() != "trx":  # TRX 不需要授权
            await self._ensure_token_approval(wallet_client, from_token, router_address, amount_in_human)

        # 9. 发送交易
        try:
            tx_payload: dict[str, Any] = {
                "to": router_address,
                "abi": SUNSWAP_SMART_ROUTER_ABI,
                "functionName": "swapExactInput",
                "args": contract_args,
                "feeLimit": 1000_000_000,  # 1000 TRX
            }
            # 如果路径起点是 TRX，需附带原生 value，与 amountIn 保持一致
            if from_token_symbol.lower() == "trx":
                # 使用基于 best_route 计算得到的 amountIn（swap_data 第 1 位）
                tx_payload["value"] = int(contract_args[4][0])

            tx_result = await wallet_client.send_transaction(cast(TronTransaction, tx_payload))

            # 兼容多种返回形态的 tx 哈希与状态
            tx_hash = (
                tx_result.get("hash") or tx_result.get("txid") or tx_result.get("transaction_id") or tx_result.get("id")
            )
            status = tx_result.get("status", "unknown")
            if isinstance(status, bool) and status:  # 兼容TronWeb
                status = "success"

            # 获取交易详情以提取实际兑换结果和费用
            actual_amount_out = None
            fee_consumed = None
            energy_used = None
            net_used = None

            if tx_hash and tx_hash != "unknown" and status == "success":
                tx_details = await self._poll_transaction_details(
                    wallet_client,
                    tx_hash,
                    to_token,
                    best_route.get("symbols", [])[-1] if best_route.get("symbols") else None,
                )
                if tx_details:
                    actual_amount_out = tx_details.get("actual_amount_out")
                    fee_consumed = tx_details.get("fee_consumed")
                    energy_used = tx_details.get("energy_used")
                    net_used = tx_details.get("net_used")

            result = {
                "success": status == "success",
                "txHash": tx_hash,
                "status": status,
                "amountIn": str(contract_args[4][0]),
                "amountOutExpected": str(best_route.get("amountOut")),
                "amountOutMinBase": str(contract_args[4][1]),
            }

            # 添加实际兑换结果和费用信息
            if actual_amount_out is not None:
                # 将实际兑换数量转换为可读的浮点数
                to_token_symbol = best_route.get("symbols", [])[-1] if best_route.get("symbols") else None
                if to_token_symbol and to_token_symbol.upper() == "TRX":
                    # TRX 固定 6 位精度
                    amount_out_human = str(Decimal(actual_amount_out) / Decimal(1_000_000))
                else:
                    # 使用钱包客户端转换为 human-readable 格式
                    try:
                        token_info = wallet_client.get_token_info_by_address(to_token)
                        decimals = token_info["decimals"]
                        amount_out_human = str(Decimal(actual_amount_out) / (Decimal(10) ** decimals))
                    except Exception:
                        # 如果获取失败，保留原始值
                        amount_out_human = str(actual_amount_out)
                result["amountOutActual"] = amount_out_human

            if fee_consumed is not None:
                # 将费用转换为 TRX（6 位精度）
                result["fee"] = str(Decimal(fee_consumed) / Decimal(1_000_000))

            if energy_used is not None:
                result["energyUsed"] = energy_used
            if net_used is not None:
                result["netUsed"] = net_used

            return result

        except Exception as e:
            raise ValueError(f"交易执行失败: {str(e)}") from e

    async def _poll_transaction_details(
        self,
        wallet_client: TronWalletBase,
        tx_hash: str,
        to_token: str,
        to_symbol: str | None,
        max_attempts: int = 60,
        poll_interval: int = 2,
    ) -> dict[str, Any] | None:
        """轮询获取交易详情，提取实际兑换量和费用信息。

        Returns:
            {
                "actual_amount_out": int | None,  # 实际兑换数量（base units）
                "fee_consumed": int | None,       # 消耗的费用（sun）
                "energy_used": int | None,        # 使用的能量
                "net_used": int | None,           # 使用的带宽
            }
        """
        import asyncio

        for attempt in range(max_attempts):
            if attempt > 0:
                await asyncio.sleep(poll_interval)

            tx_info = self._get_transaction_info(wallet_client, tx_hash)
            if tx_info:
                # 检查交易是否失败
                receipt = tx_info.get("receipt", {})
                result = receipt.get("result")

                # 如果交易失败，立即抛出异常
                if result and result != "SUCCESS":
                    contract_result = tx_info.get("contractResult", [])
                    revert_reason = tx_info.get("resMessage", "Unknown error")

                    # 尝试解析 revert 原因
                    error_msg = f"交易失败 (tx_hash={tx_hash}): {revert_reason}"
                    if contract_result:
                        error_msg += f" (contract result: {contract_result})"

                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # 提取费用信息
                fee_consumed = tx_info.get("fee", 0)
                energy_used = receipt.get("energy_usage_total", 0)
                net_used = receipt.get("net_usage", 0)

                # 从日志中提取实际兑换数量
                actual_amount_out = self._extract_swap_amount_from_logs(tx_info, to_token, to_symbol, wallet_client)

                # 如果成功获取到 actual_amount_out，停止轮询
                if actual_amount_out is not None:
                    logger.info(f"成功获取实际兑换数量，轮询次数: {attempt + 1}")
                    return {
                        "actual_amount_out": actual_amount_out,
                        "fee_consumed": fee_consumed,
                        "energy_used": energy_used,
                        "net_used": net_used,
                    }
                else:
                    logger.info(f"第 {attempt + 1} 次轮询未获取到实际兑换数量，继续等待...")

        logger.warning(f"轮询 {max_attempts} 次后仍未获取到实际兑换数量")
        return None

    async def _ensure_token_approval(
        self, wallet_client: TronWalletBase, token_address: str, spender: str, amount: str
    ) -> None:
        user_address = wallet_client.get_address()
        current_allowance = wallet_client.get_token_allowance(
            {"tokenAddress": token_address, "owner": user_address, "spender": spender}
        )

        # 将 human 数量转换为 base（sun）后再比较
        amount_base = wallet_client.convert_to_base_units(
            {
                "amount": amount,
                "tokenAddress": token_address,
            }
        )

        # 如果授权不足，进行授权
        if int(current_allowance) < int(amount_base):
            # 授权一个较大的数量以减少频繁授权
            max_uint256 = "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            await wallet_client.approve({"tokenAddress": token_address, "spender": spender, "amount": max_uint256})

    def _get_current_timestamp(self) -> int:
        """获取当前时间戳。"""
        import time

        return int(time.time())

    def _build_swap_contract_args(
        self,
        *,
        best_route: dict[str, Any],
        to_address: str,
        wallet_client: TronWalletBase,
        slippage_tolerance: float,
    ) -> list[Any]:
        path = cast(list[str], best_route["tokens"])
        pool_versions_raw = cast(list[str], best_route["poolVersions"])
        pool_version = [version for version, _ in groupby(pool_versions_raw)]

        runs = [len(list(g)) for _, g in groupby(pool_versions_raw)]
        version_len: list[int] = [runs[0] + 1] + runs[1:] if runs else [len(path)]

        # 规范化 fees 为整型列表，并确保最后一个为 0
        fees_raw = cast(list[Any], best_route["poolFees"])
        fees: list[int] = [int(f) if f != "" else 0 for f in fees_raw]
        if fees:
            fees[-1] = 0

        amount_in_human = str(best_route["amountIn"])  # human-readable
        amount_out_human = str(best_route["amountOut"])  # human-readable

        # 若路径标注了 symbols，可用来识别是否为原生 TRX
        symbols = cast(list[str] | None, best_route.get("symbols"))

        def _to_base_units(amount_human: str, token_addr: str, symbol: str | None) -> str:
            if symbol and symbol.upper() == "TRX":
                # 原生 TRX 固定 6 位
                return str(int(Decimal(amount_human) * Decimal(1_000_000)))
            return wallet_client.convert_to_base_units(
                {
                    "amount": amount_human,
                    "tokenAddress": token_addr,
                }
            )

        amount_in_base = _to_base_units(amount_in_human, path[0], symbols[0] if symbols else None)
        min_out_human = str(Decimal(amount_out_human) * Decimal(1 - slippage_tolerance))
        amount_out_min_base = _to_base_units(min_out_human, path[-1], symbols[-1] if symbols else None)

        # 统一设置 deadline 为当前时间 + 30 分钟
        deadline = int(self._get_current_timestamp()) + 1800

        swap_data = [
            int(amount_in_base),
            int(amount_out_min_base),
            to_address,
            int(deadline),
        ]

        return [path, pool_version, version_len, fees, swap_data]

    def _get_transaction_info(self, wallet_client: TronWalletBase, tx_hash: str) -> dict[str, Any] | None:
        """获取交易详情。"""
        try:
            # 使用 tronpy 的 get_transaction_info 方法
            tron_client = getattr(wallet_client, "tron", None)
            if tron_client is None:
                return None
            tx_info: Any = tron_client.get_transaction_info(tx_hash)
            return cast(dict[str, Any], tx_info) if tx_info else None
        except Exception as e:
            logger.warning(f"查询交易信息失败 (tx_hash={tx_hash}): {e}")
            return None

    def _extract_swap_amount_from_logs(
        self, tx_info: dict[str, Any], to_token: str, to_symbol: str | None, wallet_client: TronWalletBase
    ) -> int | None:
        """从交易日志中提取实际兑换数量。

        SunSwap 的 Transfer 事件格式:
        - topics[0]: Transfer 事件签名
        - topics[1]: from 地址
        - topics[2]: to 地址
        - data: 转账数量

        对于TRX兑换，有两种情况:
        1. DEX交易: 查找WTRX的Withdrawal事件
        2. SunPump交易: 从internal_transactions中提取TRX转账金额
        """
        try:
            logs = tx_info.get("log", [])

            # Transfer 事件签名: keccak256("Transfer(address,address,uint256)")
            transfer_topic = "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            # Withdrawal 事件签名: keccak256("Withdrawal(address,uint256)")
            withdrawal_topic = "7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"

            # 特殊处理：如果目标是TRX
            if to_symbol and to_symbol.upper() == "TRX":
                # 首先尝试从日志中查找WTRX的Withdrawal事件（DEX交易）
                if logs:
                    for log in logs:
                        topics = log.get("topics", [])
                        if not topics:
                            continue

                        # 检查是否为 Withdrawal 事件
                        if topics[0] == withdrawal_topic:
                            data = log.get("data", "")
                            if data:
                                # data 是十六进制字符串，转换为整数
                                amount = int(data, 16)
                                logger.info(f"从WTRX Withdrawal事件提取TRX数量: {amount} sun")
                                return amount

                # 如果没有找到Withdrawal事件，尝试从internal_transactions中提取（SunPump交易）
                internal_txs = tx_info.get("internal_transactions", [])
                if internal_txs:
                    # 获取用户地址，只统计转给用户的TRX（排除手续费）
                    user_address = wallet_client.get_address()
                    # 将地址转换为hex格式进行比较（去掉'41'前缀）
                    from tronpy.keys import to_hex_address

                    user_address_hex = to_hex_address(user_address)[2:].lower()  # 去掉'0x'前缀

                    total_trx = 0
                    for internal_tx in internal_txs:
                        # 检查接收地址是否为用户地址
                        transfer_to = internal_tx.get("transferTo_address", "")
                        if transfer_to:
                            transfer_to_hex = to_hex_address(transfer_to)[2:].lower()
                            if transfer_to_hex == user_address_hex:
                                call_value_info = internal_tx.get("callValueInfo", [])
                                for call_info in call_value_info:
                                    call_value = call_info.get("callValue", 0)
                                    if call_value > 0:
                                        total_trx += call_value

                    if total_trx > 0:
                        logger.info(f"从internal_transactions提取用户收到的TRX数量: {total_trx} sun")
                        return total_trx

                # 都没找到
                logger.warning("未找到TRX转账记录（既无WTRX Withdrawal事件，也无internal_transactions）")
                return None

            # 查找目标代币的 Transfer 事件（转给用户的）
            for log in logs:
                topics = log.get("topics", [])
                if not topics or len(topics) < 3:
                    continue

                # 检查是否为 Transfer 事件
                if topics[0] != transfer_topic:
                    continue

                # 检查是否为目标代币的合约
                log_address = log.get("address", "")

                # 简单匹配：如果地址匹配，提取数量
                if log_address.lower() == to_token.lower():
                    data = log.get("data", "")
                    if data:
                        # data 是十六进制字符串，转换为整数
                        amount = int(data, 16)
                        return amount

            return None
        except Exception as e:
            logger.warning(f"从日志提取兑换数量失败: {e}")
            return None

    def _get_sunpump_contract(self, wallet_client: TronWalletBase) -> str:
        """根据网络获取 SunPump LaunchPad 合约地址。"""
        network = wallet_client.get_network_id()
        if network == "mainnet":
            return "TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw"
        elif network == "nile":
            return "TLtTyEwqacNKc5CHLunKvxmqLB336R4Lrm"
        else:
            raise ValueError(f"不支持的网络: {network}")

    @Tool(
        {
            "name": "sunpump_purchase_token",
            "description": "Purchase SunPump token with TRX (bonding curve period)",
            "parameters_schema": PurchaseSunPumpTokenParameters,
        }
    )
    async def purchase_sunpump_token(self, wallet_client: TronWalletBase, parameters: dict[str, Any]) -> dict[str, Any]:
        """Buy SunPump token using TRX during bonding curve period."""
        from sun_agent_toolkit.plugins.sunpump.abi import LAUNCH_PAD_ABI

        # 使用统一的 swap_tokens 参数格式
        token_address = parameters["toToken"]
        trx_amount_human = parameters["amountIn"]
        slippage_tolerance = parameters.get("slippageTolerance", 0.01)
        amount_out_min_human = parameters.get("amount_out_min", "0")

        pump_contract = self._get_sunpump_contract(wallet_client)

        # 1. 检查 token 状态
        token_state = int(
            wallet_client.read(
                {
                    "address": pump_contract,
                    "abi": LAUNCH_PAD_ABI,
                    "functionName": "getTokenState",
                    "args": [token_address],
                }
            )["value"]
        )
        if token_state != 1:
            raise ValueError(f"Token is not on sale (state={token_state})")

        # 2. 转换 TRX 数量为 sun (1 TRX = 1e6 sun)
        trx_amount_sun = int(Decimal(trx_amount_human) * Decimal(1_000_000))

        # 3. 预估能获得的 token 数量（含手续费）
        result = wallet_client.read(
            {
                "address": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "getTokenAmountByPurchaseWithFee",
                "args": [token_address, trx_amount_sun],
            }
        )
        token_amount_out = int(result["value"][0])
        fee = int(result["value"][1])

        # 4. 获取 token decimals
        token_info = wallet_client.get_token_info_by_address(token_address)
        decimals = token_info["decimals"]
        token_amount_out_human = str(Decimal(token_amount_out) / (Decimal(10) ** decimals))

        # 5. 计算滑点保护
        min_out_human = str(Decimal(token_amount_out_human) * Decimal(1 - slippage_tolerance))
        if amount_out_min_human != "0":
            min_out_human = max(min_out_human, amount_out_min_human, key=lambda x: Decimal(x))
        min_out_base = int(Decimal(min_out_human) * (Decimal(10) ** decimals))

        # 6. 调用合约购买
        tx_result = await wallet_client.send_transaction(
            {
                "to": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "purchaseToken",
                "args": [token_address, min_out_base],
                "value": trx_amount_sun,
                "feeLimit": 500_000_000,
            }
        )

        tx_hash = (
            tx_result.get("hash") or tx_result.get("txid") or tx_result.get("transaction_id") or tx_result.get("id")
        )
        status = tx_result.get("status", "unknown")
        if status is True:
            status = "success"

        # 7. 获取实际兑换金额
        actual_amount_out = None
        if tx_hash and tx_hash != "unknown" and status == "success":
            actual_amount_out = await self._get_sunpump_actual_amount(wallet_client, tx_hash, token_address, decimals)

        result = {
            "success": status == "success",
            "txHash": tx_hash,
            "status": status,
            "amountIn": trx_amount_human,
            "amountOutExpected": token_amount_out_human,
            "fee": str(Decimal(fee) / Decimal(1_000_000)),
        }

        if actual_amount_out is not None:
            result["amountOutActual"] = actual_amount_out

        return result

    @Tool(
        {
            "name": "sunpump_sale_token",
            "description": "Sell SunPump token for TRX (bonding curve period)",
            "parameters_schema": SaleSunPumpTokenParameters,
        }
    )
    async def sale_sunpump_token(self, wallet_client: TronWalletBase, parameters: dict[str, Any]) -> dict[str, Any]:
        """Sell SunPump token to get TRX during bonding curve period."""
        from sun_agent_toolkit.plugins.sunpump.abi import LAUNCH_PAD_ABI

        # 使用统一的 swap_tokens 参数格式
        token_address = parameters["fromToken"]
        token_amount_human = parameters["amountIn"]
        slippage_tolerance = parameters.get("slippageTolerance", 0.01)
        amount_out_min_human = parameters.get("amount_out_min", "0")

        pump_contract = self._get_sunpump_contract(wallet_client)

        # 1. 检查 token 状态
        token_state = int(
            wallet_client.read(
                {
                    "address": pump_contract,
                    "abi": LAUNCH_PAD_ABI,
                    "functionName": "getTokenState",
                    "args": [token_address],
                }
            )["value"]
        )
        if token_state != 1:
            raise ValueError(f"Token is not on sale (state={token_state})")

        # 2. 获取 token decimals 并转换为 base units
        token_info = wallet_client.get_token_info_by_address(token_address)
        decimals = token_info["decimals"]
        token_amount_base = int(Decimal(token_amount_human) * (Decimal(10) ** decimals))

        # 3. 预估能获得的 TRX 数量（含手续费）
        result = wallet_client.read(
            {
                "address": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "getTrxAmountBySaleWithFee",
                "args": [token_address, token_amount_base],
            }
        )
        trx_amount_out = int(result["value"][0])
        fee = int(result["value"][1])
        trx_amount_out_human = str(Decimal(trx_amount_out) / Decimal(1_000_000))

        # 4. 计算滑点保护
        min_out_human = str(Decimal(trx_amount_out_human) * Decimal(1 - slippage_tolerance))
        if amount_out_min_human != "0":
            min_out_human = max(min_out_human, amount_out_min_human, key=lambda x: Decimal(x))
        min_out_base = int(Decimal(min_out_human) * Decimal(1_000_000))

        # 5. 检查并授权 token 给 LaunchPad 合约
        user_address = wallet_client.get_address()
        current_allowance = wallet_client.get_token_allowance(
            {"tokenAddress": token_address, "owner": user_address, "spender": pump_contract}
        )
        if int(current_allowance) < token_amount_base:
            max_uint256 = "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            await wallet_client.approve(
                {"tokenAddress": token_address, "spender": pump_contract, "amount": max_uint256}
            )

        # 6. 调用合约卖出
        tx_result = await wallet_client.send_transaction(
            {
                "to": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "saleToken",
                "args": [token_address, token_amount_base, min_out_base],
                "feeLimit": 500_000_000,
            }
        )

        tx_hash = (
            tx_result.get("hash") or tx_result.get("txid") or tx_result.get("transaction_id") or tx_result.get("id")
        )
        status = tx_result.get("status", "unknown")
        if status is True:
            status = "success"

        # 7. 获取实际兑换金额（TRX，固定 6 位精度）
        actual_amount_out = None
        if tx_hash and tx_hash != "unknown" and status == "success":
            actual_amount_out = await self._get_sunpump_actual_amount(
                wallet_client, tx_hash, "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb", 6
            )

        result = {
            "success": status == "success",
            "txHash": tx_hash,
            "status": status,
            "amountIn": token_amount_human,
            "amountOutExpected": trx_amount_out_human,
            "fee": str(Decimal(fee) / Decimal(1_000_000)),
        }

        if actual_amount_out is not None:
            result["amountOutActual"] = actual_amount_out

        return result

    async def _get_sunpump_actual_amount(
        self, wallet_client: TronWalletBase, tx_hash: str, token_address: str, decimals: int
    ) -> str | None:
        """从 SunPump 交易日志中获取实际兑换金额。"""
        # 判断是否为TRX（TRX地址：T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb）
        to_symbol = "TRX" if token_address == "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb" else None
        tx_details = await self._poll_transaction_details(wallet_client, tx_hash, token_address, to_symbol)

        if tx_details and tx_details.get("actual_amount_out") is not None:
            actual_amount_base = tx_details["actual_amount_out"]
            # 转换为 human-readable 格式
            amount_human = str(Decimal(actual_amount_base) / (Decimal(10) ** decimals))
            return amount_human

        return None

    def _calculate_dex_swap(self, params: dict[str, Any], wallet_client: TronWalletBase) -> dict[str, Any]:
        """计算 DEX 兑换数额（不执行交易）。"""
        from_token = cast(str, params["fromToken"])
        to_token = cast(str, params["toToken"])
        amount_in_human = cast(str, params["amountIn"])
        slippage_tolerance = cast(float, params.get("slippageTolerance", 0.005))  # 默认 0.5%

        # 1. 获取路由信息
        route_result = self.get_route(
            {
                "fromToken": from_token,
                "toToken": to_token,
                "amountIn": amount_in_human,
            },
            wallet_client,
        )

        best_route = select_best_route(route_result)
        logger.info(
            "[_calculate_dex_swap] fromToken: %s, toToken: %s, amountIn: %s, best_route: %s",
            from_token,
            to_token,
            amount_in_human,
            best_route,
        )

        # 2. 计算滑点后的最小输出
        amount_out_human = str(best_route.get("amountOut"))
        min_out_human = str(Decimal(amount_out_human) * Decimal(1 - slippage_tolerance))

        # 3. 获取 token 符号
        symbols = cast(list[str] | None, best_route.get("symbols"))
        from_symbol = symbols[0] if symbols else None
        to_symbol = symbols[-1] if symbols else None

        return {
            "fromToken": from_token,
            "toToken": to_token,
            "fromSymbol": from_symbol,
            "toSymbol": to_symbol,
            "amountIn": float(amount_in_human),
            "amountOut": float(amount_out_human),
            "amountOutMin": float(min_out_human),
            "slippageTolerance": slippage_tolerance,
            "route": best_route.get("tokens", []),
            "poolVersions": best_route.get("poolVersions", []),
            "poolFees": best_route.get("poolFees", []),
        }

    def _calculate_sunpump_purchase(self, wallet_client: TronWalletBase, params: dict[str, Any]) -> dict[str, Any]:
        """计算 SunPump token 购买数额（不执行交易）。"""
        from sun_agent_toolkit.plugins.sunpump.abi import LAUNCH_PAD_ABI

        token_address = params["toToken"]
        trx_amount_human = params["amountIn"]
        slippage_tolerance = params.get("slippageTolerance", 0.01)

        pump_contract = self._get_sunpump_contract(wallet_client)

        # 1. 检查 token 状态
        token_state = int(
            wallet_client.read(
                {
                    "address": pump_contract,
                    "abi": LAUNCH_PAD_ABI,
                    "functionName": "getTokenState",
                    "args": [token_address],
                }
            )["value"]
        )
        if token_state != 1:
            raise ValueError(f"Token is not on sale (state={token_state})")

        # 2. 转换 TRX 数量为 sun (1 TRX = 1e6 sun)
        trx_amount_sun = int(Decimal(trx_amount_human) * Decimal(1_000_000))

        # 3. 预估能获得的 token 数量（含手续费）
        result = wallet_client.read(
            {
                "address": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "getTokenAmountByPurchaseWithFee",
                "args": [token_address, trx_amount_sun],
            }
        )
        token_amount_out = int(result["value"][0])
        fee = int(result["value"][1])

        # 4. 获取 token decimals
        token_info = wallet_client.get_token_info_by_address(token_address)
        decimals = token_info["decimals"]
        token_amount_out_human = str(Decimal(token_amount_out) / (Decimal(10) ** decimals))

        # 5. 计算滑点保护
        min_out_human = str(Decimal(token_amount_out_human) * Decimal(1 - slippage_tolerance))

        return {
            "fromToken": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",  # TRX
            "toToken": token_address,
            "fromSymbol": "TRX",
            "toSymbol": token_info.get("symbol", "UNKNOWN"),
            "amountIn": float(trx_amount_human),
            "amountOut": float(token_amount_out_human),
            "amountOutMin": float(min_out_human),
            "slippageTolerance": slippage_tolerance,
            "fee": str(Decimal(fee) / Decimal(1_000_000)),
            "tradingMethod": "SunPump Bonding Curve",
        }

    def _calculate_sunpump_sale(self, wallet_client: TronWalletBase, params: dict[str, Any]) -> dict[str, Any]:
        """计算 SunPump token 卖出数额（不执行交易）。"""
        from sun_agent_toolkit.plugins.sunpump.abi import LAUNCH_PAD_ABI

        token_address = params["fromToken"]
        token_amount_human = params["amountIn"]
        slippage_tolerance = params.get("slippageTolerance", 0.01)

        pump_contract = self._get_sunpump_contract(wallet_client)

        # 1. 检查 token 状态
        token_state = int(
            wallet_client.read(
                {
                    "address": pump_contract,
                    "abi": LAUNCH_PAD_ABI,
                    "functionName": "getTokenState",
                    "args": [token_address],
                }
            )["value"]
        )
        if token_state != 1:
            raise ValueError(f"Token is not on sale (state={token_state})")

        # 2. 获取 token decimals 并转换为 base units
        token_info = wallet_client.get_token_info_by_address(token_address)
        decimals = token_info["decimals"]
        token_amount_base = int(Decimal(token_amount_human) * (Decimal(10) ** decimals))

        # 3. 预估能获得的 TRX 数量（含手续费）
        result = wallet_client.read(
            {
                "address": pump_contract,
                "abi": LAUNCH_PAD_ABI,
                "functionName": "getTrxAmountBySaleWithFee",
                "args": [token_address, token_amount_base],
            }
        )
        trx_amount_out = int(result["value"][0])
        fee = int(result["value"][1])
        trx_amount_out_human = str(Decimal(trx_amount_out) / Decimal(1_000_000))

        # 4. 计算滑点保护
        min_out_human = str(Decimal(trx_amount_out_human) * Decimal(1 - slippage_tolerance))

        return {
            "fromToken": token_address,
            "toToken": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",  # TRX
            "fromSymbol": token_info.get("symbol", "UNKNOWN"),
            "toSymbol": "TRX",
            "amountIn": float(token_amount_human),
            "amountOut": float(trx_amount_out_human),
            "amountOutMin": float(min_out_human),
            "slippageTolerance": slippage_tolerance,
            "fee": str(Decimal(fee) / Decimal(1_000_000)),
            "tradingMethod": "SunPump Bonding Curve",
        }

    def _get_sunpump_token_state(self, wallet_client: TronWalletBase, token_address: str) -> int:
        """获取 SunPump token 状态。返回 0=未创建, 1=售卖中, 2=待发射, 3=已发射。"""
        try:
            from sun_agent_toolkit.plugins.sunpump.abi import LAUNCH_PAD_ABI

            pump_contract = self._get_sunpump_contract(wallet_client)
            token_state = int(
                wallet_client.read(
                    {
                        "address": pump_contract,
                        "abi": LAUNCH_PAD_ABI,
                        "functionName": "getTokenState",
                        "args": [token_address],
                    }
                )["value"]
            )
            return token_state
        except Exception:
            # 如果查询失败，假设不是 SunPump token，返回已发射状态
            return 3
