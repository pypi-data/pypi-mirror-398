import asyncio
import json
import logging
import time
import traceback
from collections.abc import Awaitable, Callable
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from tronpy import Tron, keys
from tronpy.defaults import conf_for_name
from tronpy.exceptions import TransactionNotFound
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.tron import Transaction

from sun_agent_toolkit.core.classes.wallet_client_base import Balance, Signature
from sun_agent_toolkit.core.types.token import Token

from .abi import TRC20_ABI
from .tokens import TronToken
from .tron_wallet_base import TronWalletBase
from .types import TronReadRequest, TronReadResult, TronTransaction

logger = logging.getLogger(__name__)


class TronWalletClient(TronWalletBase):
    """Concrete implementation of TRON wallet client."""

    def __init__(
        self,
        private_key: str | None = None,
        *,
        public_key: str | None = None,
        network: str = "mainnet",
        api_key: str | None = None,
        tokens: list[TronToken] | None = None,
        enable_send: bool = True,
        send_func: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
        sign_func: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
    ):
        """Initialize the TRON wallet implementation.

        Args:
            private_key: Private key in hex format (without 0x prefix)
            public_key: Base58 TRON address to operate in read-only mode when private key is unavailable
            network: TRON network ("mainnet", "shasta", "nile")
            tokens: List of token configurations
            enable_send: Whether to enable send functionality
        """
        if (private_key is None) == (public_key is None):
            raise ValueError("Exactly one of private_key or public_key must be provided")

        can_sign = private_key is not None or send_func is not None
        effective_enable_send = enable_send and can_sign

        super().__init__(tokens, effective_enable_send)
        if enable_send and not can_sign:
            logger.warning("Disabling send functionality because no private key was provided")

        self.network = network

        # Initialize TRON client; 标注为 Any 以屏蔽库未注解成员访问的告警
        self.tron: Any = None
        if api_key is None:
            self.tron = Tron(network=network)
        else:
            provider = HTTPProvider(conf_for_name(network), timeout=10, api_key=api_key)
            self.tron = Tron(provider=provider)

        # Setup private key
        self.priv_key: PrivateKey | None = None
        self._address: str | None = None

        if private_key is not None:
            pk_hex = private_key[2:] if private_key.startswith("0x") else private_key
            try:
                self.priv_key = PrivateKey(bytes.fromhex(pk_hex))
            except Exception as e:
                raise ValueError(f"Invalid private key format: {e}") from e

            pk_pub: Any = self.priv_key.public_key
            self._address = pk_pub.to_base58check_address()
        else:
            # public_key 限定为 Base58 地址
            assert public_key is not None
            pub_input = public_key.strip()
            try:
                hex_addr = keys.to_hex_address(pub_input)
                self._address = keys.to_base58check_address(hex_addr)
            except Exception as e:
                raise ValueError("Invalid TRON address provided as public_key") from e
        self.send_func = send_func
        self.sign_func = sign_func

        logger.info(f"Initialized TRON wallet: {self._address} on {network}")

    def get_address(self) -> str:
        """Get the wallet's public address."""
        assert self._address is not None
        return self._address

    def get_network_id(self) -> str:
        """Get the network ID (e.g., 'mainnet', 'shasta', 'nile')."""
        return self.network

    async def get_transaction_receipt(self, params: dict[str, Any]) -> dict[str, Any]:
        get_transaction_info = self.tron.trx.client.get_transaction_info
        if params.get("solid", False):
            get_transaction_info = self.tron.trx.client.get_solid_transaction_info
        end_time = time.time() + params.get("timeout", 30)
        interval = params.get("interval", 1.6)
        while time.time() < end_time:
            try:
                receipt = get_transaction_info(params["tx_hash"])
                return {"status": receipt.get("result", "SUCCESS"), "receipt": receipt}
            except TransactionNotFound:
                await asyncio.sleep(interval)
                continue
            except Exception as e:
                logger.error(traceback.format_exc())
                raise ValueError(f"Failed to get transaction receipt: {e}") from e
        raise ValueError("Failed to get transaction receipt: timeout")

    def get_transaction_url(self, tx_hash: str) -> str:
        """Get the tronscan url of transaction."""
        BASE_URLS = {
            "mainnet": "https://tronscan.org/#/",
            "nile": "https://nile.tronscan.org/#/",
        }
        base_url = BASE_URLS.get(self.get_network_id())
        if not base_url:
            raise ValueError(f"network {self.get_network_id()} is not supported")
        return f"{base_url}transaction/{tx_hash}"

    @staticmethod
    def _parse_transaction_error(error: str) -> str:
        try:
            return bytes.fromhex(error).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return error
        except Exception:
            logger.error(traceback.format_exc())
            return error

    async def sign_transaction(self, unsigned_txn: dict[str, Any]) -> dict[str, Any]:
        """Sign a transaction with the wallet's private key. returns signed transaction"""
        if not self.enable_send:
            raise ValueError("Private key is required to sign messages")
        try:
            if self.priv_key:
                transaction = Transaction.from_json(unsigned_txn)
                signed_txn = transaction.sign(self.priv_key)
                return signed_txn.to_json()
            else:
                assert self.sign_func is not None
                res = await self.sign_func({"tx": unsigned_txn})
                success = bool(res.get("success"))
                if success and "tx" in res:
                    return cast(dict[str, Any], res.get("tx", {}))
                else:
                    raise RuntimeError(self._parse_transaction_error(res.get("error", "unknown error")))
        except Exception as e:
            logger.error(f"Transaction signing failed: {e}")
            raise ValueError(f"Failed to sign transaction: {str(e)}") from e

    async def broadcast_transaction(self, txn: dict[str, Any]) -> dict[str, str]:
        """Boardcast a transaction with the wallet's private key."""
        try:
            transaction = Transaction.from_json(txn, self.tron.trx.client)
            receipt = transaction.broadcast()
            receipt.wait()
            tx_id: str | None = None
            if isinstance(receipt, dict):
                rec_dict = cast(dict[str, Any], receipt)
                tx_id = rec_dict.get("txid") or rec_dict.get("transaction_id") or rec_dict.get("id")
            else:
                tx_id = getattr(receipt, "txid", None) or getattr(receipt, "transaction_id", None)
            return {"hash": tx_id or "unknown", "status": "success"}
        except Exception as e:
            logger.error(f"Transaction signing failed: {e}")
            raise ValueError(f"Failed to sign transaction: {str(e)}") from e

    async def sign_message(self, message: str) -> Signature:
        """Sign a message with the wallet's private key."""
        if not self.enable_send:
            raise ValueError("Private key is required to sign messages")
        try:
            message_bytes = message.encode("utf-8")
            if self.priv_key:
                signature = self.priv_key.sign_msg(message_bytes)
                return {"signature": signature.hex()}
            else:
                assert self.sign_func is not None
                res = await self.sign_func({"message": message_bytes})
                success = bool(res.get("success"))
                signature = res.get("signature")
                if success and isinstance(signature, str):
                    return {"signature": signature}
                else:
                    raise RuntimeError(self._parse_transaction_error(res.get("error", "unknown error")))
        except Exception as e:
            logger.error(f"Message signing failed: {e}")
            raise ValueError(f"Failed to sign message: {str(e)}") from e

    async def sign_typed_data(
        self, types: dict[str, Any], primary_type: str, domain: dict[str, Any], value: dict[str, Any]
    ) -> Signature:
        """Sign typed data with the wallet's private key (TRON equivalent of EIP-712)."""
        if not self.enable_send:
            raise ValueError("Private key is required to sign typed data")
        try:
            structured_message = {"types": types, "primaryType": primary_type, "domain": domain, "message": value}
            message_str = str(structured_message)
            return await self.sign_message(message_str)
        except Exception as e:
            logger.error(f"Typed data signing failed: {e}")
            raise ValueError(f"Failed to sign typed data: {str(e)}") from e

    def build_transaction(self, transaction: TronTransaction) -> dict[str, str]:
        """Build a transaction on the TRON chain."""
        try:
            step_any: Any = None
            txn: Any = None
            # Decide fee limit once (SUN); default 500 TRX
            fee_limit_raw: Any = transaction.get("feeLimit", 500_000_000)
            fee_limit_opt = int(fee_limit_raw) if isinstance(fee_limit_raw, int | str) else 500_000_000
            if "functionName" in transaction:
                # Smart contract interaction: load contract and set ABI if provided
                contract: Any = self.tron.get_contract(transaction["to"])  # tronpy 未注解，类型为 Any
                abi_opt = transaction.get("abi")
                if abi_opt is not None:
                    # 显式设置 ABI，支持 ABIEncoderV2 的编码
                    contract.abi = abi_opt

                # Generic contract call
                method: Any = getattr(contract.functions, transaction["functionName"])  # ContractMethod
                call_args = transaction.get("args", [])
                value_opt = transaction.get("value", 0)
                # For payable methods, attach native TRX via with_transfer before invoking
                if value_opt > 0:
                    method = method.with_transfer(value_opt)
                step_any = method(*call_args).with_owner(self._address)
                step_any = step_any.fee_limit(fee_limit_opt)
                txn = step_any.build()
            else:
                # Native TRX transfer - must build before signing
                value = int(transaction.get("value", 0))
                step_any = self.tron.trx.transfer(self._address, transaction["to"], value)
                step_any = step_any.fee_limit(fee_limit_opt)
                txn = step_any.build()
            return txn.to_json()
        except Exception as e:
            logger.error(f"Build failed: {e}")
            raise ValueError(f"Failed to build transaction: {str(e)}") from e

    async def send_transaction(self, transaction: TronTransaction) -> dict[str, str]:
        """Send a transaction on the TRON chain."""
        if not self.enable_send:
            raise ValueError("Private key is required to send transactions")
        try:
            step_any: Any = None
            txn: Any = None
            # Decide fee limit once (SUN); default 500 TRX
            fee_limit_raw: Any = transaction.get("feeLimit", 500_000_000)
            fee_limit_opt = int(fee_limit_raw) if isinstance(fee_limit_raw, int | str) else 500_000_000
            if "functionName" in transaction:
                # Smart contract interaction: load contract and set ABI if provided
                contract: Any = self.tron.get_contract(transaction["to"])  # tronpy 未注解，类型为 Any
                abi_opt = transaction.get("abi")
                if abi_opt is not None:
                    # 显式设置 ABI，支持 ABIEncoderV2 的编码
                    contract.abi = abi_opt

                if transaction["functionName"] == "transfer":
                    # TRC20 transfer
                    args = transaction.get("args", [])
                    recipient, amount = args[0], args[1]
                    step_any = contract.functions.transfer(recipient, amount).with_owner(self._address)
                    step_any = step_any.fee_limit(fee_limit_opt)
                    txn = step_any.build()
                elif transaction["functionName"] == "approve":
                    # TRC20 approve
                    args = transaction.get("args", [])
                    spender, amount = args[0], args[1]
                    step_any = contract.functions.approve(spender, amount).with_owner(self._address)
                    step_any = step_any.fee_limit(fee_limit_opt)
                    txn = step_any.build()
                else:
                    # Generic contract call
                    method: Any = getattr(contract.functions, transaction["functionName"])  # ContractMethod
                    call_args = transaction.get("args", [])
                    value_opt = int(transaction.get("value", 0) or 0)
                    # For payable methods, attach native TRX via with_transfer before invoking
                    if value_opt > 0:
                        method = method.with_transfer(value_opt)
                    step_any = method(*call_args).with_owner(self._address)
                    step_any = step_any.fee_limit(fee_limit_opt)
                    txn = step_any.build()
            else:
                # Native TRX transfer - must build before signing
                value = int(transaction.get("value", 0))
                step_any = self.tron.trx.transfer(self._address, transaction["to"], value)
                step_any = step_any.fee_limit(fee_limit_opt)
                txn = step_any.build()

            if self.send_func is not None:
                res = await self.send_func(txn.to_json())
                status = res.get("success")
                if not status:
                    raise RuntimeError(self._parse_transaction_error(res.get("error", "unknown error")))
                return {"hash": res.get("txid", "unknown"), "status": status}
            # Sign and broadcast
            signed_txn: Any = txn.sign(self.priv_key)
            result: Any = signed_txn.broadcast()

            # Wait for confirmation
            receipt: Any = result.wait()

            # Extract transaction ID from receipt - support multiple shapes
            tx_id: str | None = None
            if isinstance(receipt, dict):
                rec_dict = cast(dict[str, Any], receipt)
                tx_id = rec_dict.get("txid") or rec_dict.get("transaction_id") or rec_dict.get("id")
            else:
                tx_id = getattr(receipt, "txid", None) or getattr(receipt, "transaction_id", None)

            # Fallback to signed transaction's txid
            if not tx_id and hasattr(signed_txn, "txid"):
                tx_id = signed_txn.txid

            # Final fallback
            if not tx_id:
                tx_id = "unknown"

            logger.info(f"Transaction completed: {tx_id}")

            # Check transaction status from receipt
            status = "success"  # Default assumption
            if isinstance(receipt, dict):
                # Check for failure indicators in receipt
                rec_any: dict[str, Any] = cast(dict[str, Any], receipt)
                if rec_any.get("result") == "FAILED" or rec_any.get("ret", [{}])[0].get("contractRet") == "REVERT":
                    status = "failed"

            return {"hash": tx_id, "status": status}

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise ValueError(f"Failed to send transaction: {str(e)}") from e

    def _apply_transaction_options(self, builder_any: Any, options: dict[str, Any] | None) -> Any:
        """Apply optional transaction builder settings such as fee limit, memo, permission, expiration."""
        if not options:
            return builder_any

        fee_limit_opt = options.get("feeLimit") or options.get("fee_limit")
        if fee_limit_opt is not None:
            builder_any = builder_any.fee_limit(int(fee_limit_opt))

        memo_opt = options.get("memo")
        if memo_opt:
            builder_any = builder_any.memo(memo_opt)

        permission_opt = options.get("permissionId") or options.get("permission_id")
        if permission_opt is not None:
            builder_any = builder_any.permission_id(int(permission_opt))

        expiration_opt = options.get("expiration")
        if expiration_opt is not None:
            builder_any = builder_any.expiration(int(expiration_opt))

        return builder_any

    def _normalize_transaction_payload(self, payload: dict[str, Any] | str) -> dict[str, Any]:
        """Convert tool input into a transaction JSON dictionary."""
        if isinstance(payload, dict):
            return payload

        if not isinstance(payload, str):
            raise TypeError("transaction payload must be dict or JSON string")

        text = payload.strip()
        if not text:
            raise ValueError("transaction payload is empty")

        try:
            return cast(dict[str, Any], json.loads(text))
        except json.JSONDecodeError as exc:
            raise ValueError("transaction payload string must be valid JSON") from exc

    def _hex_address(self) -> str:
        if self._address is None:
            raise ValueError("Wallet address is not initialized")
        return keys.to_hex_address(self._address)

    def get_account_resource_info(self) -> dict[str, Any]:
        res: dict[str, Any] = cast(dict[str, Any], self.tron.get_account_resource(self._address))
        resource_info = res.copy()
        resource_info["freeNetUsed"] = res.get("freeNetUsed", 0)
        resource_info["freeNetLimit"] = res.get("freeNetLimit", 600)
        resource_info["NetUsed"] = res.get("NetUsed", 0)
        resource_info["NetLimit"] = res.get("NetLimit", 0)
        resource_info["EnergyUsed"] = res.get("EnergyUsed", 0)
        resource_info["EnergyLimit"] = res.get("EnergyLimit", 0)

        resource_info["NetUsedIncludeFree"] = resource_info["NetUsed"] + resource_info["freeNetUsed"]
        resource_info["NetLimitIncludeFree"] = resource_info["NetLimit"] + resource_info["freeNetLimit"]
        return resource_info

    def get_account_info(self, params: dict[str, Any]) -> dict[str, Any]:
        address = params.get("address", self._address)
        account = cast(dict[str, Any], self.tron.get_account(address))
        return account

    def get_pending_reward(self) -> int:
        res = cast(
            dict[str, Any], self.tron.provider.make_request("wallet/getReward", {"address": self._hex_address()})
        )
        reward_any = res.get("reward", 0)
        try:
            return int(reward_any)
        except Exception:
            return 0

    def get_stake_info(self) -> dict[str, Any]:
        try:
            account = cast(dict[str, Any], self.tron.get_account(self._address))
        except Exception as e:
            logger.error(f"Failed to get stake info: {e}")
            raise ValueError(f"Failed to fetch stake info: {str(e)}") from e

        account_resource = account.get("account_resource", {})
        delegated_energy_v1_amount = account_resource.get("frozen_balance_for_energy", {}).get("frozen_balance", 0)
        delegated_energy_v2_amount = account_resource.get("delegated_frozenV2_balance_for_energy", 0)
        delegated_bandwidth_v2_amount = account.get("delegated_frozenV2_balance_for_bandwidth", 0)
        frozen_entries = cast(list[dict[str, Any]] | None, account.get("frozenV2")) or []
        unfrozen_entries = cast(list[dict[str, Any]] | None, account.get("unfrozenV2")) or []

        def _normalize(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, dict[str, int]]:
            normalized: list[dict[str, Any]] = []
            total = 0
            by_resource: dict[str, int] = {
                "ENERGY": 0,
                "BANDWIDTH": 0,
            }
            for entry in entries:
                resource_type: str = entry.get("type", "BANDWIDTH")
                amount_value: int = entry.get("amount", 0)
                if resource_type not in ("ENERGY", "BANDWIDTH"):
                    continue
                normalized_entry = dict(entry)
                normalized_entry["type"] = resource_type
                normalized_entry["amount"] = amount_value
                normalized.append(normalized_entry)
                total += amount_value
                by_resource[resource_type] += amount_value
            return normalized, total, by_resource

        frozen_list, frozen_total, frozen_by_resource = _normalize(frozen_entries)
        delegated_out_total = delegated_energy_v1_amount + delegated_energy_v2_amount + delegated_bandwidth_v2_amount

        delegated_out_by_resource: dict[str, Any] = {}
        delegated_out_by_resource["ENERGY"] = delegated_energy_v1_amount + delegated_energy_v2_amount
        delegated_out_by_resource["BANDWIDTH"] = delegated_bandwidth_v2_amount
        frozen_by_resource["ENERGY_INCLUDE_DELEGATED"] = (
            frozen_by_resource["ENERGY"] + delegated_out_by_resource["ENERGY"]
        )
        frozen_by_resource["BANDWIDTH_INCLUDE_DELEGATED"] = (
            frozen_by_resource["BANDWIDTH"] + delegated_out_by_resource["BANDWIDTH"]
        )

        def _sun_totals_to_trx(data: dict[str, int]) -> dict[str, str]:
            return {k: str(Decimal(v) / Decimal(1_000_000)) for k, v in data.items()}

        tron_power = (frozen_total + delegated_out_total) // 1_000_000

        # 计算可提取的未质押TRX
        withdrawable_sun = 0
        current_timestamp = int(time.time() * 1000)  # 毫秒时间戳

        for entry in unfrozen_entries:
            unfreeze_expire_time = entry.get("unfreeze_expire_time", 0)
            amount = entry.get("unfreeze_amount", 0)

            # 如果已过锁定期（当前时间 >= 过期时间），则可以提取
            if current_timestamp >= unfreeze_expire_time:
                try:
                    withdrawable_sun += int(amount)
                except Exception:
                    pass

        return {
            "tronPower": tron_power,
            "frozen": frozen_list,
            "totalFrozen": frozen_total,
            "totalFrozenUnit": "sun",
            "totalFrozenIncludeDelegated": tron_power,
            "frozenByResource": frozen_by_resource,
            "totalDelegatedOut": delegated_out_total,
            "delegatedOutByResource": delegated_out_by_resource,
            "withdrawableUnstaked": withdrawable_sun,
            "totalFrozenTrx": tron_power,
            "sun_to_trx": "1 trx = 1000000 sun"
        }

    def get_votes(self) -> dict[str, int]:
        account = cast(dict[str, Any], self.tron.get_account(self._address))

        # 已用票数
        votes_list = cast(list[dict[str, Any]] | None, account.get("votes")) or []
        used_votes = 0
        for v in votes_list:
            try:
                used_votes += int(v.get("voteCount") or v.get("vote_count") or 0)
            except Exception:
                continue

        # 总票数
        account_resource = account.get("account_resource", {})
        delegated_energy_v1_amount = account_resource.get("frozen_balance_for_energy", {}).get("frozen_balance", 0)
        delegated_energy_v2_amount = account_resource.get("delegated_frozenV2_balance_for_energy", 0)
        delegated_bandwidth_v2_amount = account.get("delegated_frozenV2_balance_for_bandwidth", 0)
        frozen_entries = cast(list[dict[str, Any]], account.get("frozenV2", []))
        total_sun = delegated_energy_v1_amount + delegated_energy_v2_amount + delegated_bandwidth_v2_amount
        for entry in frozen_entries:
            resource_type: str = entry.get("type", "BANDWIDTH")
            amount_value: int = entry.get("amount", 0)
            if resource_type not in ("ENERGY", "BANDWIDTH"):
                continue
            total_sun += amount_value

        total_votes = total_sun // 1_000_000

        available = total_votes - used_votes
        if available < 0:
            available = 0

        return {
            "totalVotes": int(total_votes),
            "availableVotes": int(available),
        }

    def list_witnesses(self) -> list[dict[str, Any]]:
        try:
            res: Any = self.tron.provider.make_request("wallet/listwitnesses", {})
        except Exception as e:
            logger.error(f"Failed to list witnesses: {e}")
            raise ValueError(f"Failed to fetch witnesses: {str(e)}") from e

        witness_list = cast(list[dict[str, Any]] | None, res.get("witnesses")) or []
        normalized: list[dict[str, Any]] = []
        total_votes = 0
        for entry in witness_list:
            item = dict(entry)
            address_raw = item.get("address")
            if isinstance(address_raw, str):
                try:
                    if address_raw.startswith("T") and len(address_raw) == 34:
                        address_base58 = address_raw
                    else:
                        address_base58 = keys.to_base58check_address(address_raw)
                    item["address"] = address_base58
                except Exception:
                    pass
            vote_raw = item.get("voteCount")
            if vote_raw is None:
                vote_raw = item.get("vote_count")
            if vote_raw is None:
                item["voteCount"] = 0
            else:
                try:
                    item["voteCount"] = int(vote_raw)
                except Exception:
                    item["voteCount"] = 0
            try:
                total_votes += int(item["voteCount"])
            except Exception:
                pass

            produced_raw = item.get("totalProduced")
            if produced_raw is None:
                produced_raw = item.get("total_produced")
            missed_raw = item.get("totalMissed")
            if missed_raw is None:
                missed_raw = item.get("total_missed")
            if produced_raw is not None and missed_raw is not None:
                try:
                    produced = int(produced_raw)
                    missed = int(missed_raw)
                    rounds = produced + missed
                    if rounds > 0:
                        item["productionRatio"] = produced / rounds
                except Exception:
                    pass

            latest_raw = item.get("latestBlockNumber")
            if latest_raw is None:
                latest_raw = item.get("latest_block_num")
            if latest_raw is None:
                item.pop("latestBlockNumber", None)
            else:
                try:
                    item["latestBlockNumber"] = int(latest_raw)
                except Exception:
                    item.pop("latestBlockNumber", None)
            normalized.append(item)
        if total_votes > 0:
            for item in normalized:
                try:
                    vote_count = int(item.get("voteCount") or 0)
                    item["voteShare"] = vote_count / total_votes
                except Exception:
                    continue
        return normalized

    def read(self, request: TronReadRequest) -> TronReadResult:
        """Read data from a smart contract."""
        try:
            # Validate contract address format
            contract_addr = request["address"]
            if not contract_addr or len(contract_addr) != 34 or not contract_addr.startswith("T"):
                raise ValueError(f"Invalid TRON contract address format: {contract_addr}")
            contract = self.tron.get_contract(contract_addr)
            abi = request.get("abi")
            if abi:
                contract.abi = abi

            # Get the function from the contract
            func = getattr(contract.functions, request["functionName"])

            # Call the function with provided arguments
            call_args = request.get("args", [])
            func_result = func(*call_args)
            # Some functions return direct values, others return callable objects
            if hasattr(func_result, "call"):
                result = func_result.call()
            else:
                result = func_result

            return {"value": result}

        except Exception as e:
            logger.error(f"Contract read failed for {request.get('address', 'unknown')}: {e}")
            # Check if it's a specific problematic contract on testnet
            if "bad base58check format" in str(e) and request.get("address") == "TFbqCqAJtoJGNqKxcJrHpj7dPNPyaUwrLn":
                raise ValueError(
                    f"Contract {request['address']} appears to be invalid or non-existent on {self.network} network"
                ) from e
            raise ValueError(f"Failed to read from contract: {str(e)}") from e

    def get_delegated_resource(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            info = self.get_account_resource_info()
            energy_weight = info.get("TotalEnergyWeight", 0)
            energy_limit = info.get("TotalEnergyLimit", 0)
            energy_price = energy_weight / energy_limit
            bandwidth_weight = info.get("TotalNetWeight", 0)
            bandwidth_limit = info.get("TotalNetLimit", 0)
            bandwidth_price = bandwidth_weight / bandwidth_limit

            from_address = params.get("from_address") or self._address
            to_address = params["to_address"]
            result = self.tron.get_delegated_resource_v2(from_address, to_address)
            delegated = result.get("delegatedResource", [])
            response = {
                "energy_delegated_trx_in_base_units_total": 0,
                "energy_delegated_trx_in_base_units_available": 0,
                "energy_delegated_amount_total": 0,
                "energy_delegated_amount_available": 0,
                "energy_trx_price": energy_price,
                "bandwidth_delegated_trx_in_base_units_total": 0,
                "bandwidth_delegated_trx_in_base_units_available": 0,
                "bandwidth_delegated_amount_total": 0,
                "bandwidth_delegated_amount_available": 0,
                "bandwidth_trx_price": bandwidth_price,
                "delegated_resources": [],
            }
            now = datetime.now().timestamp() * 1000
            for delegate_info in delegated:
                energy_trx = delegate_info.get("frozen_balance_for_energy", 0)
                response["energy_delegated_trx_in_base_units_total"] += energy_trx
                energy_expiration = delegate_info.get("expire_time_for_energy")
                if energy_expiration is None or energy_expiration <= now:
                    response["energy_delegated_trx_in_base_units_available"] += energy_trx
                if energy_trx > 0:
                    delegated_energy: dict[str, Any] = {
                        "type": "ENERGY",
                        "from": delegate_info["from"],
                        "to": delegate_info["to"],
                    }
                    delegated_energy["delegated_trx_in_base_units"] = energy_trx
                    delegated_energy["delegated_resource_amount"] = (
                        energy_trx / 1_000_000 / energy_price if energy_price > 0 else 0.0
                    )
                    if energy_expiration is not None:
                        delegated_energy["expire_time"] = energy_expiration
                    response["delegated_resources"].append(delegated_energy)

                bandwidth_trx = delegate_info.get("frozen_balance_for_bandwidth", 0)
                response["bandwidth_delegated_trx_in_base_units_total"] += bandwidth_trx
                bandwidth_expiration = delegate_info.get("expire_time_for_bandwidth")
                if bandwidth_expiration is None or bandwidth_expiration <= now:
                    response["bandwidth_delegated_trx_in_base_units_available"] += bandwidth_trx
                if bandwidth_trx > 0:
                    delegated_bandwidth: dict[str, Any] = {
                        "type": "BANDWIDTH",
                        "from": delegate_info["from"],
                        "to": delegate_info["to"],
                    }
                    delegated_bandwidth["delegated_trx_in_base_units"] = bandwidth_trx
                    delegated_bandwidth["delegated_resource_amount"] = (
                        bandwidth_trx / 1_000_000 / bandwidth_price if bandwidth_price > 0 else 0.0
                    )
                    if bandwidth_expiration is not None:
                        delegated_bandwidth["expire_time"] = bandwidth_expiration
                    response["delegated_resources"].append(delegated_bandwidth)
            if energy_price > 0:
                response["energy_delegated_amount_total"] = (
                    response["energy_delegated_trx_in_base_units_total"] / 1_000_000 / energy_price
                )
                response["energy_delegated_amount_available"] = (
                    response["energy_delegated_trx_in_base_units_available"] / 1_000_000 / energy_price
                )
            if bandwidth_price > 0:
                response["bandwidth_delegated_amount_total"] = (
                    response["bandwidth_delegated_trx_in_base_units_total"] / 1_000_000 / bandwidth_price
                )
                response["bandwidth_delegated_amount_available"] = (
                    response["bandwidth_delegated_trx_in_base_units_available"] / 1_000_000 / bandwidth_price
                )
            return response
        except Exception as e:
            logger.error(traceback.format_exc())
            raise ValueError(f"Failed to get delegated resource: {e}") from e

    def get_native_balance(self) -> int:
        """Get the native balance of the wallet in SUN."""
        return self.get_native_balance_of(self._address)

    def get_native_balance_of(self, address: str | None) -> int:
        """Get the native balance of given wallet address in SUN."""
        try:
            account = cast(dict[str, Any], self.tron.get_account(address))
            balance_sun = account.get("balance", 0)
            return balance_sun
        except Exception as e:
            logger.error(f"Failed to get native balance: {e}")
            raise ValueError(f"Failed to fetch native balance: {str(e)}") from e

    def balance_of(self, address: str, token_address: str | None = None) -> Balance:
        """Get the balance of an address for native or TRC20 tokens.

        Args:
            address: The address to check balance for
            token_address: Optional TRC20 token address

        Returns:
            Balance information
        """
        if token_address and token_address != "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb":
            try:
                balance_result = self.read(
                    {
                        "address": token_address,
                        "abi": TRC20_ABI,
                        "functionName": "balanceOf",
                        "args": [address],
                    }
                )
                balance_in_base_units = str(balance_result["value"])

                token_info = self.get_token_info_by_address(token_address)

                # Use proper decimal arithmetic to avoid precision loss
                divisor = Decimal(10) ** token_info["decimals"]
                balance_value = str(Decimal(balance_in_base_units) / divisor)

                return {
                    "decimals": token_info["decimals"],
                    "symbol": token_info["symbol"],
                    "name": token_info["name"],
                    "value": balance_value,
                    "in_base_units": balance_in_base_units,
                }
            except Exception as e:
                raise ValueError(f"Failed to fetch token balance: {str(e)}") from e
        else:
            try:
                balance_in_sun = self.get_native_balance_of(address)
                decimals = 6
                balance_value = str(Decimal(balance_in_sun) / (10**decimals))

                return {
                    "decimals": decimals,
                    "symbol": "TRX",
                    "name": "TRON",
                    "value": balance_value,
                    "in_base_units": str(balance_in_sun),
                }
            except Exception as e:
                raise ValueError(f"Failed to fetch native balance: {str(e)}") from e

    def get_token_info_by_address(self, address: str | None) -> Token:
        """Get token information by token address.

        Args:
            address: The token base58 address, None for native token

        Returns:
            Token information
        """
        chain = self.get_chain()
        network = cast(str, chain["network"])

        if address is None or address == "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb":
            return {
                "symbol": "TRX",
                "decimals": 6,
                "name": "TRON",
                "address": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
            }

        for token in self.tokens:
            if network not in token["networks"] or token["networks"][network]["contractAddress"] != address:
                continue
            return {
                "symbol": token["symbol"],
                "decimals": token["decimals"],
                "name": token["name"],
                "address": address,
            }

        try:
            decimals_result = self.read({"address": address, "abi": TRC20_ABI, "functionName": "decimals", "args": []})
            name_result = self.read({"address": address, "abi": TRC20_ABI, "functionName": "name", "args": []})
            symbol_result = self.read({"address": address, "abi": TRC20_ABI, "functionName": "symbol", "args": []})
            return {
                "symbol": str(symbol_result["value"]),
                "decimals": int(decimals_result["value"]),
                "name": str(name_result["value"]),
                "address": address,
            }
        except Exception as e:
            logger.error(f"Failed to get token info {e}")
            raise ValueError(f"Token with address {address} not found") from e

    def get_token_info_by_ticker(self, ticker: str) -> Token:
        """Get token information by ticker symbol.

        Args:
            ticker: The token ticker symbol (e.g., USDT, USDC)

        Returns:
            Token information
        """
        chain = self.get_chain()
        network = cast(str, chain["network"])
        upper_ticker = ticker.upper()

        if upper_ticker == "TRX":
            return {
                "symbol": "TRX",
                "decimals": 6,
                "name": "TRON",
                "address": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
            }

        for token in self.tokens:
            if token["symbol"].upper() == upper_ticker:
                if network in token["networks"]:
                    return {
                        "symbol": token["symbol"],
                        "decimals": token["decimals"],
                        "name": token["name"],
                        "address": token["networks"][network]["contractAddress"],
                    }

        # TODO: deal with sunio & sunpump token

        raise ValueError(f"Token with ticker {ticker} not found for network {network}")

    # ----- Stake 2.0 & Governance implementations -----

    async def _finalize_transaction(self, builder_any: Any) -> dict[str, str]:
        """Helper to build, sign, broadcast and wait a transaction, returning a uniform receipt dict."""
        try:
            txn: Any = builder_any.build()
            if self.send_func is not None:
                res = await self.send_func(txn.to_json())
                status = res.get("success")
                if not status:
                    raise RuntimeError(self._parse_transaction_error(res.get("error", "unknown error")))
                return {"hash": res.get("txid", "unknown"), "status": status}
            signed_txn: Any = txn.sign(self.priv_key)
            result: Any = signed_txn.broadcast()
            receipt: Any = result.wait()

            tx_id: str | None = None
            if isinstance(receipt, dict):
                rec_dict = cast(dict[str, Any], receipt)
                tx_id = rec_dict.get("txid") or rec_dict.get("transaction_id") or rec_dict.get("id")
            else:
                tx_id = getattr(receipt, "txid", None) or getattr(receipt, "transaction_id", None)
            if not tx_id and hasattr(signed_txn, "txid"):
                tx_id = signed_txn.txid
            if not tx_id:
                tx_id = "unknown"

            status = "success"
            if isinstance(receipt, dict):
                rec_any: dict[str, Any] = cast(dict[str, Any], receipt)
                if rec_any.get("result") == "FAILED" or rec_any.get("ret", [{}])[0].get("contractRet") == "REVERT":
                    status = "failed"
            logger.info(f"Transaction completed: {tx_id}")
            return {"hash": tx_id, "status": status}
        except Exception as e:
            logger.error(f"Finalizing transaction failed: {e}")
            raise

    async def freeze_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Freeze TRX to obtain ENERGY or BANDWIDTH (Stake 2.0)."""
        try:
            amount = int(params["amountInSun"])
            resource = params["resource"]
            builder_any: Any = self.tron.trx.freeze_balance(self._address, amount, resource)
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"freeze_balance failed: {e}")
            raise ValueError(f"Failed to freeze balance: {str(e)}") from e

    async def unfreeze_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Unstake TRX (Stake 2.0)."""
        try:
            resource = params["resource"]
            amount_opt = int(params.get("amountInSun", "0"))
            if amount_opt == 0:
                raise RuntimeError("Can't unfreeze balance amount 0")
            builder_any = self.tron.trx.unfreeze_balance(
                owner=self._address, resource=resource, unfreeze_balance=amount_opt
            )
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"unfreeze_balance failed: {e}")
            raise ValueError(f"Failed to unfreeze balance: {str(e)}") from e

    async def withdraw_stake_balance(self, params: dict[str, Any]) -> dict[str, str]:
        """Withdraw expired unstaked TRX after cool-down period (Stake 2.0)."""
        del params  # unused
        try:
            # TronPy API: withdraw_stake_balance(owner)
            builder_any: Any = self.tron.trx.withdraw_stake_balance(self._address)
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"withdraw_stake_balance failed: {e}")
            raise ValueError(f"Failed to withdraw expired unstake: {str(e)}") from e

    async def delegate_resource(self, params: dict[str, Any]) -> dict[str, str]:
        """Delegate ENERGY/BANDWIDTH to another address (Stake 2.0)."""
        try:
            receiver = params["receiver"]
            amount = int(params["amountInSun"])
            resource = params["resource"]
            lock = params["lock"]
            lock_period = params.get("lock_period")
            builder_any: Any = self.tron.trx.delegate_resource(
                self._address, receiver, amount, resource, lock=lock, lock_period=lock_period
            )
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"delegate_resource failed: {e}")
            raise ValueError(f"Failed to delegate resource: {str(e)}") from e

    async def undelegate_resource(self, params: dict[str, Any]) -> dict[str, str]:
        """Cancel delegation of ENERGY/BANDWIDTH (Stake 2.0)."""
        try:
            receiver = params["receiver"]
            amount = int(params["amountInSun"])
            resource = params["resource"]
            builder_any: Any = self.tron.trx.undelegate_resource(self._address, receiver, amount, resource)
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"undelegate_resource failed: {e}")
            raise ValueError(f"Failed to undelegate resource: {str(e)}") from e

    async def vote_witness(self, params: dict[str, Any]) -> dict[str, str]:
        """Vote for witnesses (governance)."""
        try:
            votes_param = params["votes"]
            # Expect list of {witnessAddress, voteCount}
            votes_list: list[tuple[str, int]] = []
            for v in votes_param:
                addr = cast(str, v.get("witnessAddress"))
                count = int(cast(int, v.get("voteCount")))
                votes_list.append((addr, count))
            builder_any: Any = self.tron.trx.vote_witness(self._address, *votes_list)
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"vote_witness failed: {e}")
            raise ValueError(f"Failed to vote witnesses: {str(e)}") from e

    async def withdraw_rewards(self, params: dict[str, Any]) -> dict[str, str]:
        """Withdraw voting rewards."""
        del params  # unused
        try:
            builder_any: Any = self.tron.trx.withdraw_rewards(self._address)
            builder_any = builder_any.with_owner(self._address)
            return await self._finalize_transaction(builder_any)
        except Exception as e:
            logger.error(f"withdraw_rewards failed: {e}")
            raise ValueError(f"Failed to withdraw rewards: {str(e)}") from e
