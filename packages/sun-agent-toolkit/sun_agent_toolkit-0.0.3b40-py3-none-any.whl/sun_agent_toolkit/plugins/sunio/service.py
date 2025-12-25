import json
import logging
from typing import Any

import aiohttp

from sun_agent_toolkit.core.decorators.tool import Tool
from sun_agent_toolkit.core.types.token import Token

from .parameters import (
    SearchTokenParameters,
)

logger = logging.getLogger(__name__)


class SunIOService:
    def __init__(self, base_url: str, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present

    async def _make_request(self, endpoint: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Make a request to the SunIO API."""
        url = f"{self.base_url}/{endpoint}"

        headers: dict[str, Any] = {}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=parameters, headers=headers) as response:
                    response_text = await response.text()
                    try:
                        response_json = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from {endpoint}: {response_text}") from e

                    logger.debug(f"\nAPI Response for {endpoint}:")
                    logger.debug(f"Status: {response.status}")
                    logger.debug(f"Headers: {dict(response.headers)}")
                    logger.debug(f"Body: {response_text}")

                    if not response.ok or response_json.get("code", -1) != 0:
                        error = response_json.get("msg", "Unknown error")
                        raise Exception(error)

                    return response_json
            except aiohttp.ClientError as e:
                raise Exception(f"Network error while accessing {endpoint}: {str(e)}") from e

    @Tool(
        {
            "name": "sunio_search_token_by_symbol",
            "description": "search sunio token by token symbol",
            "parameters_schema": SearchTokenParameters,
        }
    )
    async def search_token(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """search sunio token by token symbol"""
        try:
            response = await self._make_request(
                "tokens/search",
                {
                    "query": parameters["symbol"],
                    "protocol": "ALL",
                    "sort": "reserveUsd",
                    "pageSize": parameters["top_n"],
                    "pageNo": "1",
                },
            )

            # If no approval data is returned, the token is already approved
            if not response or "data" not in response or not response["data"]["list"]:
                return {"success": True, "tokens": []}

            tokens: list[Token] = [
                {
                    "name": token["tokenName"],
                    "symbol": token["tokenSymbol"],
                    "address": token["tokenAddress"],
                    "decimals": token["tokenDecimal"],
                }
                for token in response["data"]["list"]
            ]
            return {"success": True, "tokens": tokens}
        except Exception as error:
            raise Exception(f"Failed to search token: {error}") from error
