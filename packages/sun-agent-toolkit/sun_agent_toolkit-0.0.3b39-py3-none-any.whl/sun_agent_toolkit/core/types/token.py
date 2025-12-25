from typing import TypedDict


class Token(TypedDict):
    name: str
    symbol: str
    address: str
    decimals: int
