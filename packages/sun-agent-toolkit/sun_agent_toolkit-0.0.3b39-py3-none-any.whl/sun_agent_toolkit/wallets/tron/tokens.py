from typing import TypedDict, cast

from sun_agent_toolkit.core.types.token import Token as CoreToken


class TronTokenChainInfo(TypedDict):
    """TRON token information for specific network"""

    contractAddress: str


class TronToken(CoreToken):
    """TRON token with network-specific contract addresses"""

    networks: dict[str, TronTokenChainInfo]  # network -> token info


# TRON mainnet tokens
SUN_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "SUN",
        "symbol": "SUN",
        "decimals": 18,
        "networks": {"mainnet": {"contractAddress": "TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S"}},
    },
)

SUNOLD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "SUNOLD",
        "symbol": "SUNOLD",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TKkeiboTkxXKJpbmVFbv4a8ov5rAfRDMf9"},
            "nile": {"contractAddress": "TWrZRHY9aKQZcyjpovdH6qeCEyYZrRQDZt"},
        },
    },
)

NFT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "APENFT",
        "symbol": "NFT",
        "decimals": 6,
        "networks": {"mainnet": {"contractAddress": "TFczxzPhnThNSqr5by8tvxsdCFRRz6cPNq"}},
    },
)

AINFT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "APENFT",
        "symbol": "AINFT",
        "decimals": 6,
        "networks": {"mainnet": {"contractAddress": "TFczxzPhnThNSqr5by8tvxsdCFRRz6cPNq"}},
    },
)

BTC_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Bitcoin",
        "symbol": "BTC",
        "decimals": 8,
        "networks": {
            "mainnet": {"contractAddress": "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9"},
            "nile": {"contractAddress": "TG9XJ75ZWcUw69W8xViEJZQ365fRupGkFP"},
        },
    },
)

WBTC_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Wrapped BTC",
        "symbol": "WBTC",
        "decimals": 8,
        "networks": {"mainnet": {"contractAddress": "TYhWwKpw43ENFWBTGpzLHn3882f2au7SMi"}},
    },
)

WBTT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Wrapped BitTorrent",
        "symbol": "WBTT",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TKfjV9RNKJJCqPvBtK8L7Knykh7DNWvnYt"},
            "nile": {"contractAddress": "TLELxLrgD3dq6kqS4x6dEGJ7xNFMbzK95U"},
        },
    },
)

WTRX_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Wrapped TRX",
        "symbol": "WTRX",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR"},
            "nile": {"contractAddress": "TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a"},
        },
    },
)

USDT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Tether USD",
        "symbol": "USDT",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"},
            "nile": {"contractAddress": "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"},
        },
    },
)

USDC_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8"},
            "nile": {"contractAddress": "TUpMhErZL2fhh4sVNULAbNKLokS4GjC1F4"},
        },
    },
)

BTT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "BitTorrent",
        "symbol": "BTT",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4"},
        },
    },
)

JST_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "JUST GOV v1.0",
        "symbol": "JST",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9"},
            "nile": {"contractAddress": "TF17BgPaZYbz8oxbjhriubPDsA7ArKoLX3"},
        },
    },
)

WIN_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "WINK",
        "symbol": "WIN",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU7"},
            "nile": {"contractAddress": "TNDSHKGBmgRx9mDYA9CnxPx55nu672yQw2"},
        },
    },
)

USDJ_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "JUST Stablecoin v1.0",
        "symbol": "USDJ",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TMwFHYXLJaRUPeW6421aqXL4ZEzPRFGkGT"},
            "nile": {"contractAddress": "TLBaRhANQoJFTqre9Nf1mjuwNWjCJeYqUL"},
        },
    },
)

TUSD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "TrueUSD",
        "symbol": "TUSD",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TUpMhErZL2fhh4sVNULAbNKLokS4GjC1F4"},
            "nile": {"contractAddress": "TRz7J6dD2QWxBoumfYt4b3FaiRG23pXfop"},
        },
    },
)

LTC_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Litecoin",
        "symbol": "LTC",
        "decimals": 8,
        "networks": {
            "mainnet": {"contractAddress": "TR3DLthpnDdCGabhVDbD3VMsiJoCXY3bZd"},
        },
    },
)

HT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "HuobiToken",
        "symbol": "HT",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TDyvndWuvX5xTBwHPYJi7J3Yq8pq8yh62h"},
            "nile": {"contractAddress": "TGfVzt44kg6ZJ4fUqpHzJy3Jb37YMf8pMH"},
        },
    },
)

STRX_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "staked TRX",
        "symbol": "sTRX",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TU3kjFuhtEo42tsCBtfYUAZxoqQ4yuSLQ5"},
        },
    },
)

STUSDT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Staked USDT",
        "symbol": "stUSDT",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TThzxNRLrW2Brp9DcTQU8i4Wd9udCWEdZ3"},
            "nile": {"contractAddress": "TVUGRzuUBoUmFvuHFfgyrFS39PDtEDHfX9"},
        },
    },
)

HTX_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "HTX",
        "symbol": "HTX",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TUPM7K8REVzD2UdV4R5fe5M8XbnR2DdoJ6"},
        },
    },
)

SUNDOG_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Sundog",
        "symbol": "SUNDOG",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TXL6rJbvmjD46zeN1JssfgxvSo99qC8MRT"},
        },
    },
)

SUNCAT_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "SUNCAT",
        "symbol": "SUNCAT",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TAwAg9wtQzTMFsijnSFotJrpxhMm3AqW1d"},
        },
    },
)

BULL_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Tron Bull",
        "symbol": "BULL",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TAt4ufXFaHZAEV44ev7onThjTnF61SEaEM"},
        },
    },
)

SUNDOGE_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "SUNDOGE",
        "symbol": "SUNDOGE",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TAz6oGWhsmHPp7Ap6khmAYxjfHFYokqdQ4"},
        },
    },
)

TRONKEY_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "TRONKEY",
        "symbol": "TRONKEY",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TRHsKfoPJxFHnJ4wJ8Zc9nmSNAyaNYqff7"},
        },
    },
)

CZC_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Crypto Zillion Club",
        "symbol": "CZC",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TRJBN2ninnLKUUDR1f686goCYetPcPed8f"},
        },
    },
)

PUSS_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "PUSS",
        "symbol": "PUSS",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TX5eXdf8458bZ77fk8xdvUgiQmC3L93iv7"},
        },
    },
)

AFRO_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Afro",
        "symbol": "Afro",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TDnXXUXH37zEojEfrvYziS6yKSpYmkdjHE"},
        },
    },
)

TBULL_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Tron Bull",
        "symbol": "TBULL",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TPeoxx1VhUMnAUyjwWfximDYFDQaxNQQ45"},
        },
    },
)

USDCOLD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "USD Coin Old",
        "symbol": "USDCOLD",
        "decimals": 6,
        "networks": {
            "mainnet": {"contractAddress": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8"},
            "nile": {"contractAddress": "TWMCMCoJPqCGw5RR7eChF2HoY3a9B8eYA3"},
        },
    },
)

ETHB_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Ethereum BTTC-Bridged",
        "symbol": "ETHB",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TRFe3hT5oYhjSZ6f3ji5FJ7YCfrkWnHRvh"},
        },
    },
)

ETH_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Ethereum",
        "symbol": "ETH",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "THb4CqiFdwNHsWsQCs4JhzwjMWys4aqCbF"},
            "nile": {"contractAddress": "TQz9i4JygMCzizdVu8NE4BdqesrsHv1L93"},
        },
    },
)

LABR_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Labrador",
        "symbol": "LABR",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TMEvVHCUngZ6JfuvnH74cX8UFw1KedAuhR"},
        },
    },
)

LFD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "LifeDay",
        "symbol": "LFD",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TWG5VrJicAspqrNfii93AoqsJ7wnJRheex"},
        },
    },
)

PEPE_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "PePe",
        "symbol": "PePe",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TMacq4TDUw5q8NFBwmbY4RLXvzvG5JTkvi"},
        },
    },
)

USDDOLD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Decentralized USD OLD",
        "symbol": "USDDOLD",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn"},
        },
    },
)

USDD_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "Decentralized USD",
        "symbol": "USDD",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TXDk8mbtRbXeYuMNS83CfKPaYYT8XWv9Hz"},
            "nile": {"contractAddress": "TGjgvdTWWrybVLaVeFqSyVqJQWjxqRYbaK"},
        },
    },
)

HTXUNION_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "HTXunion",
        "symbol": "HTXunion",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TWekqrSXkWw3D5Hup1xoEVcykcBcxX6yh4"},
        },
    },
)

USD1_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "World Liberty Financial USD",
        "symbol": "USD1",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TPFqcBAaaUMCSVRCqPaQ9QnzKhmuoLR6Rc"},
        },
    },
)

TRUMP_TRC20: TronToken = cast(
    TronToken,
    {
        "name": "OFFICIAL TRUMP",
        "symbol": "TRUMP",
        "decimals": 18,
        "networks": {
            "mainnet": {"contractAddress": "TXZQuyCasxN42bjAcYpP2xwYVMCF6gHBnv"},
        },
    },
)

# Predefined tokens list
PREDEFINED_TOKENS: list[TronToken] = [
    USDT_TRC20,
    USDC_TRC20,
    BTT_TRC20,
    JST_TRC20,
    SUN_TRC20,
    WIN_TRC20,
]

SUNSWAP_TOKEN_LIST: list[TronToken] = [
    SUN_TRC20,
    BTT_TRC20,
    SUNOLD_TRC20,
    AINFT_TRC20,
    NFT_TRC20,
    BTC_TRC20,
    WBTC_TRC20,
    WBTT_TRC20,
    WTRX_TRC20,
    JST_TRC20,
    WIN_TRC20,
    USDT_TRC20,
    USDJ_TRC20,
    TUSD_TRC20,
    LTC_TRC20,
    HT_TRC20,
    STRX_TRC20,
    STUSDT_TRC20,
    HTX_TRC20,
    SUNDOG_TRC20,
    SUNCAT_TRC20,
    BULL_TRC20,
    SUNDOGE_TRC20,
    TRONKEY_TRC20,
    CZC_TRC20,
    PUSS_TRC20,
    AFRO_TRC20,
    TBULL_TRC20,
    USDCOLD_TRC20,
    ETHB_TRC20,
    ETH_TRC20,
    LABR_TRC20,
    LFD_TRC20,
    PEPE_TRC20,
    USDDOLD_TRC20,
    USDD_TRC20,
    HTXUNION_TRC20,
    USD1_TRC20,
    TRUMP_TRC20,
]


def get_token_by_symbol(symbol: str, network: str = "mainnet") -> TronToken | None:
    """Get token by symbol for specific network"""
    for token in PREDEFINED_TOKENS:
        if token["symbol"] == symbol and network in token["networks"]:
            return token
    return None


def get_token_by_address(address: str, network: str = "mainnet") -> TronToken | None:
    """Get token by contract address for specific network"""
    for token in PREDEFINED_TOKENS:
        if network in token["networks"] and token["networks"][network]["contractAddress"] == address:
            return token
    return None
