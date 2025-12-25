import asyncio
import logging
from typing import Any

import aiohttp

from sun_agent_toolkit.core.decorators.tool import Tool

from .parameters import (
    GetAccountInfoParameters,
    GetAccountTransactionsParameters,
    GetRankingParameters,
    GetTokenHoldersParameters,
    GetTokenInfoParameters,
    GetTokenMarketParameters,
    GetTransactionParameters,
    GetTronStatsParameters,
    GetWitnessesParameters,
    SearchTronParameters,
)

logger = logging.getLogger(__name__)


class TronScanService:
    def __init__(self, base_url: str, api_key: str | None = None):
        need_key = "apilist.tronscanapi.com" in base_url
        if need_key and not api_key:
            raise ValueError("TronScan API key is required for this endpoint. Please provide TRONSCAN_API_KEY.")
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"User-Agent": "Sun-Agent-Toolkit/1.0", "Accept": "application/json"}
        if api_key:
            self.headers["TRON-PRO-API-KEY"] = api_key

    async def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make HTTP request to TronScan API"""
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                logger.debug("TronScan GET %s params=%s", url, params)
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"TronScan API error! Status: {response.status}, Response: {error_text}")
            except aiohttp.ClientError as e:
                raise Exception(f"Network error when calling TronScan API: {str(e)}") from e

    @staticmethod
    def _to_number(value: Any) -> float | None:
        try:
            return float(value)
        except Exception:
            return None

    @Tool(
        {
            "name": "tronscan_get_witnesses_in_detail",
            "description": "Get the list of witnesses",
            "parameters_schema": GetWitnessesParameters,
        }
    )
    async def get_witnesses(self, parameters: dict[str, Any]) -> dict[str, Any]:
        witness_type = int(parameters["witness_type"])
        top_n = int(parameters["top_n"])
        try:
            response: dict[str, Any] = await self._make_request("/pagewitness", {"witness_type": witness_type})
            num = min(response["total"], top_n)
            return {"num": num, "witnesses": response["data"][:num]}
        except Exception as e:
            return {"error": str(e)}

    @Tool(
        {
            "name": "tronscan_get_account_info",
            "description": "Get detailed account information from TronScan including balance and tokens",
            "parameters_schema": GetAccountInfoParameters,
        }
    )
    async def get_account_info(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get detailed account information from TronScan"""
        address = parameters["address"]
        include_tokens = parameters.get("include_tokens", True)

        try:
            # Get basic account info
            account_data: dict[str, Any] = await self._make_request("/account", {"address": address})

            result: dict[str, Any] = {"address": address, "basic_info": account_data}

            # Get token balances if requested
            if include_tokens:
                try:
                    token_data: dict[str, Any] = await self._make_request(
                        "/account/tokens", {"address": address, "start": 0, "limit": 50}
                    )
                    result["tokens"] = token_data
                except Exception as e:
                    result["tokens_error"] = str(e)

            return result

        except Exception as e:
            return {"error": str(e), "address": address}

    @Tool(
        {
            "description": "Get detailed transaction information from TronScan",
            "parameters_schema": GetTransactionParameters,
        }
    )
    async def get_transaction(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get detailed transaction information from TronScan"""
        tx_hash = parameters["tx_hash"]

        try:
            data: dict[str, Any] = await self._make_request("/transaction-info", {"hash": tx_hash})
            return {"transaction_hash": tx_hash, "data": data}
        except Exception as e:
            return {"error": str(e), "transaction_hash": tx_hash}

    @Tool(
        {
            "description": "Get transaction history for a TRON address from TronScan",
            "parameters_schema": GetAccountTransactionsParameters,
        }
    )
    async def get_account_transactions(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get transaction history for a TRON address"""
        address = parameters["address"]
        limit = min(parameters.get("limit", 20), 200)  # Cap at 200
        start = parameters.get("start", 0)
        sort = parameters.get("sort", "-timestamp")
        only_confirmed = parameters.get("only_confirmed", True)

        try:
            params: dict[str, Any] = {"sort": sort, "count": "true", "limit": limit, "start": start, "address": address}

            if only_confirmed:
                params["confirmed"] = "true"

            data: dict[str, Any] = await self._make_request("/transaction", params)

            return {
                "address": address,
                "transactions": data.get("data", []),
                "total": data.get("total", 0),
                "pagination": {"start": start, "limit": limit, "has_more": len(data.get("data", [])) == limit},
            }

        except Exception as e:
            return {"error": str(e), "address": address}

    @Tool(
        {
            "name": "tronscan_get_token_info_in_detail",
            "description": "Get TRC20 token information by token address from TronScan including price, volume, transfers etc.",
            "parameters_schema": GetTokenInfoParameters,
        }
    )
    async def get_token_info(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get TRC20 token information from TronScan"""
        contract_address = parameters["contract_address"]

        try:
            data: dict[str, Any] = await self._make_request("/token_trc20", {"contract": contract_address})
            if "total" not in data or data["total"] == 0 or "trc20_tokens" not in data:
                return {"error": "TRC20 not found", "contract_address": contract_address}
            return {"contract_address": contract_address, "token_info": data["trc20_tokens"][0]}
        except Exception as e:
            return {"error": str(e), "contract_address": contract_address}

    @Tool(
        {
            "name": "tronscan_get_token_holders",
            "description": "Get top holders of token by token address from TronScan",
            "parameters_schema": GetTokenHoldersParameters,
        }
    )
    async def get_token_holders(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get token holders information from TronScan"""
        contract_address = parameters["contract_address"]
        limit = min(parameters.get("limit", 20), 100)  # Cap at 100
        start = parameters.get("start", 0)

        try:
            params: dict[str, Any] = {"contract_address": contract_address, "start": start, "limit": limit}

            data: dict[str, Any] = await self._make_request("/token_trc20/holders", params) or {}
            holders = data.get("trc20_tokens", [])
            total = data.get("total", 0)

            return {
                "contract_address": contract_address,
                "holders": holders,
                "total_holders": total,
                "pagination": {"start": start, "limit": limit, "has_more": len(holders) < total},
            }

        except Exception as e:
            return {"error": str(e), "contract_address": contract_address}

    @Tool({"description": "Get TRON network statistics from TronScan", "parameters_schema": GetTronStatsParameters})
    async def get_tron_stats(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get TRON network statistics from TronScan"""
        try:
            # Get multiple stats endpoints
            stats_tasks: list[Any] = [
                self._make_request("/system/status"),
                self._make_request("/stats/overview"),
            ]

            try:
                results: list[Any] = await asyncio.gather(*stats_tasks, return_exceptions=True)

                response: dict[str, Any] = {"network_stats": {}}

                if not isinstance(results[0], Exception):
                    response["network_stats"]["system_status"] = results[0]

                if not isinstance(results[1], Exception):
                    response["network_stats"]["overview"] = results[1]

                return response

            except Exception as e:
                return {"error": f"Failed to gather network stats: {str(e)}"}

        except Exception as e:
            return {"error": str(e)}

    @Tool(
        {
            "name": "tronscan_search_tron",
            "description": "Search TRON blockchain data using /api/search/v2.",
            "parameters_schema": SearchTronParameters,
        }
    )
    async def search_tron(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Search TRON blockchain data using /api/search/v2 (search_key + optional search_type)."""
        search_key = parameters["search_key"]
        search_type = parameters.get("search_type", "token") or "token"
        start = 0
        limit = 10  # API max 50

        try:
            params: dict[str, Any] = {
                "term": search_key,
                "type": search_type,
                "start": start,
                "limit": limit,
            }
            data: dict[str, Any] = await self._make_request("/search/v2", params)
            return {
                "search_key": search_key,
                "search_type": search_type,
                "start": start,
                "limit": limit,
                "results": data,
            }
        except Exception as e:
            return {"error": str(e), "search_key": search_key}

    @Tool(
        {
            "name": "tronscan_get_token",
            "description": "Get TRC20 token market data (price, volume, market cap, holders).",
            "parameters_schema": GetTokenMarketParameters,
        }
    )
    async def get_token(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get TRC20 token market info from TronScan."""
        token = parameters["token"]

        try:
            # Decide endpoint based on token format (TRC10 id is numeric)
            if token.isdigit():
                response = await self._make_request("/token", {"id": token})
                candidates = response.get("data") or response.get("tokens") or []
            else:
                response = await self._make_request("/token_trc20", {"contract": token})
                candidates = response.get("trc20_tokens") or response.get("data") or []

            token_info: dict[str, Any] | None = None
            if isinstance(candidates, list) and candidates:
                token_info = candidates[0]
            elif isinstance(response, dict):
                token_info = response

            if not token_info:
                return {"error": "Token not found", "token": token}

            def pick(obj: dict[str, Any], *keys: str) -> Any:
                for key in keys:
                    if key in obj and obj[key] is not None:
                        return obj[key]
                return None

            price_trx = self._to_number(pick(token_info, "priceInTrx", "priceInTRX", "price_trx", "latest_price_trx"))
            price_usd = self._to_number(pick(token_info, "priceInUsd", "price_usd", "price", "usd_price"))
            if price_usd is None and price_trx is not None:
                price_usd = price_trx / 1  # keep as-is if USD missing; caller may provide context

            result = {
                "name": pick(token_info, "name", "tokenName"),
                "symbol": pick(token_info, "symbol", "tokenAbbr", "tokenSymbol", "abbr"),
                "price_usd": price_usd,
                "price_trx": price_trx,
                "change_24h": self._to_number(
                    pick(token_info, "change24h", "percentChange24h", "priceChange24h", "gain")
                ),
                "volume_24h": self._to_number(pick(token_info, "volume24h", "volume24H", "total_volume_24h")),
                "market_cap": self._to_number(pick(token_info, "marketCap", "market_cap", "marketCapUsd")),
                "holders": pick(token_info, "holders_count", "holdersCount", "nrOfTokenHolders"),
            }
            return result
        except Exception as e:
            return {"error": str(e), "token": token}

    @Tool(
        {
            "name": "tronscan_get_ranking",
            "description": "Get TronScan ranking (Top TRC20 tokens) via /tokens/overview.",
            "parameters_schema": GetRankingParameters,
        }
    )
    async def get_ranking(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Get ranking list from TronScan /tokens/overview."""
        sort_by_raw = str(parameters.get("sortBy", "marketCapUsd"))
        allowed_sort_fields = {"priceInTrx", "gain", "volume24hInTrx", "holderCount", "marketcap"}
        sort_field = sort_by_raw if sort_by_raw in allowed_sort_fields else "marketCapUsd"

        order = str(parameters.get("order", "desc")).lower()
        limit = max(1, min(int(parameters.get("limit", 10)), 500))  # API limit up to 500
        print(limit)
        try:
            response = await self._make_request(
                "/tokens/overview/web",
                {
                    "start": 0,
                    "limit": limit,
                    "order": order,
                    "filter": "trc20",
                    "sort": sort_field,
                    "verifier": "all",
                },
            )
            raw_items = response.get("tokens") or []
            print(len(raw_items))
            items: list[dict[str, Any]] = []
            for obj in raw_items:
                if not isinstance(obj, dict):
                    continue
                items.append(obj)  # keep even if fields are missing

            def pick(obj: dict[str, Any], *keys: str) -> Any:
                for key in keys:
                    if key in obj and obj[key] is not None:
                        return obj[key]
                return None

            def numeric_value(obj: dict[str, Any]) -> float:
                key_map = {
                    "priceInTrx": ("priceInTrx", "priceInTRX", "price_trx", "latest_price_trx"),
                    "gain": ("gain", "change24h", "percentChange24h", "priceChange24h"),
                    "volume24hInTrx": ("volume24hInTrx", "volume24h", "volume24H", "total_volume_24h"),
                    "holderCount": ("holderCount", "holders_count", "holdersCount", "nrOfTokenHolders"),
                    "marketcap": ("marketcap", "marketCap", "market_cap", "marketCapUsd"),
                }
                for key in key_map.get(sort_field, (sort_field,)):
                    val = self._to_number(obj.get(key))
                    if val is not None:
                        return val
                return 0.0

            def build_item(obj: dict[str, Any]) -> dict[str, Any]:
                price_trx = self._to_number(pick(obj, "priceInTrx", "priceInTRX", "price_trx", "latest_price_trx"))
                price_usd = self._to_number(pick(obj, "priceInUsd", "price_usd", "price", "usd_price"))
                if price_usd is None and price_trx is not None:
                    price_usd = price_trx

                return {
                    "name": pick(obj, "name", "tokenName"),
                    "symbol": pick(obj, "symbol", "tokenAbbr", "tokenSymbol", "abbr"),
                    "contract_address": pick(obj, "contractAddress", "contractAddressLower"),
                    "price_usd": price_usd,
                    "price_trx": price_trx,
                    "change_24h": self._to_number(pick(obj, "change24h", "percentChange24h", "priceChange24h", "gain")),
                    "volume_24h": self._to_number(
                        pick(obj, "volume24hInTrx", "volume24h", "volume24H", "total_volume_24h")
                    ),
                    "market_cap": self._to_number(pick(obj, "marketcap", "marketCap", "market_cap", "marketCapUsd")),
                    "holders": pick(obj, "holderCount", "holders_count", "holdersCount", "nrOfTokenHolders"),
                }

            return {"sortBy": sort_field, "items": [build_item(obj) for obj in items]}
        except Exception as e:
            return {"error": str(e), "sortBy": sort_field}
