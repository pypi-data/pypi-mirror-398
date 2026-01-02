from typing import List
import aiohttp
from typing import Dict, List, Optional


class API:
    DEXSC = "DexScreener"
    GECKO = "GeckoTerminal"


class Token:
    def __init__(self, address: str, name: str, symbol: str) -> None:
        self.address = address
        self.name = name
        self.symbol = symbol

    @classmethod
    def from_dict(cls, token_dict: Dict[str, str]) -> "Token":
        return cls(token_dict["address"], token_dict["name"], token_dict["symbol"])


class Transaction:
    def __init__(self, buys: int, sells: int) -> None:
        self.buys = buys
        self.sells = sells

    @classmethod
    def from_dict(cls, txn_dict: Dict[str, int]) -> "Transaction":
        return cls(txn_dict["buys"], txn_dict["sells"])


class Volume:
    def __init__(self, h1: int, h24: int) -> None:
        self.h1 = h1
        self.h24 = h24

    @classmethod
    def from_dict(cls, volume_dict: Dict[str, int]) -> "Volume":
        return cls(volume_dict["h1"], volume_dict["h24"])


class PriceChange:
    def __init__(self, h1: int, h24: int) -> None:
        self.h1 = h1
        self.h24 = h24

    @classmethod
    def from_dict(cls, price_change_dict: Dict[str, int]) -> "PriceChange":
        return cls(
            price_change_dict["h1"],
            price_change_dict["h24"],
        )


class Pair:
    def __init__(
        self,
        api: str,
        chainId: str,
        dexId: str,
        url: str,
        pairAddress: str,
        baseToken: Token,
        quoteToken: Token,
        priceNative: str,
        txns: Dict[str, Transaction],
        volume: Volume,
        priceChange: PriceChange,
        labels: List[str] = [],
        priceUsd: Optional[str] = None,
        liquidity: Optional[float] = None,
        fdv: Optional[int] = None,
        telegram: Optional[str] = None,
        twitter: Optional[str] = None,
        website: Optional[str] = None,
    ) -> None:
        self.api = api
        self.chainId = chainId
        self.dexId = dexId
        self.url = url
        self.pairAddress = pairAddress
        self.baseToken = baseToken
        self.quoteToken = quoteToken
        # self.priceNative = priceNative
        self.priceNative = None
        self.priceUsd = priceUsd
        self.txns = None
        self.volume = volume
        self.priceChange = priceChange
        self.labels = labels
        self.liquidity = liquidity
        self.fdv = fdv
        self.telegram = telegram
        self.twitter = twitter
        self.website = website

    @classmethod
    def from_dict(cls, pair_dict: dict) -> "Pair":
        base_token = Token(
            pair_dict["baseToken"]["address"],
            pair_dict["baseToken"]["name"],
            pair_dict["baseToken"]["symbol"],
        )
        quote_token = Token(
            pair_dict["quoteToken"]["address"],
            pair_dict["quoteToken"]["name"],
            pair_dict["quoteToken"]["symbol"],
        )
        # txns = (
        #     {
        #         key: Transaction(value["buys"], value["sells"])
        #         for key, value in pair_dict["txns"].items()
        #     }
        #     if pair_dict["txns"]
        #     else None
        # )
        txns = None
        # volume = (
        #     Volume(pair_dict["volume"]["h1"], pair_dict["volume"]["h24"])
        #     if pair_dict["volume"]
        #     else None
        # )
        volume = None
        # price_change = (
        #     PriceChange(pair_dict["priceChange"]["h1"], pair_dict["priceChange"]["h24"])
        #     if pair_dict["priceChange"]
        #     else None
        # )
        price_change = None
        liquidity = pair_dict.get("liquidity", 0)

        return Pair(
            pair_dict["api"],
            pair_dict["chainId"],
            pair_dict["dexId"],
            pair_dict["url"],
            pair_dict["pairAddress"],
            base_token,
            quote_token,
            # pair_dict["priceNative"],
            0,
            txns,
            volume,
            price_change,
            pair_dict["labels"],
            pair_dict["priceUsd"],
            liquidity,
            pair_dict["fdv"],
            pair_dict["telegram"],
            pair_dict["twitter"],
            pair_dict["website"],
        )

    @staticmethod
    def from_dexsc_dict(pair_dict: Dict):
        try:
            print(pair_dict)
            base_token = Token.from_dict(pair_dict["baseToken"])
            quote_token = Token.from_dict(pair_dict["quoteToken"])
            # txns = (
            #     {
            #         key: Transaction.from_dict(value)
            #         for key, value in pair_dict["txns"].items()
            #         if key not in ["m5", "h6"]
            #     }
            #     if pair_dict["txns"]
            #     else None
            # )
            txns = None
            # volume = (
            #     Volume.from_dict(pair_dict["volume"]) if pair_dict["volume"] else None
            # )
            volume = None
            # price_change = (
            #     PriceChange.from_dict(pair_dict["priceChange"])
            #     if pair_dict["priceChange"]
            #     else None
            # )
            price_change = None
            liquidity_info = pair_dict.get("liquidity", {})
            liquidity = liquidity_info.get("usd", 0) if liquidity_info else 0

            # Handle fdv more safely, ensuring it is converted to an int
            fdv = pair_dict.get("fdv")
            fdv = int(fdv) if fdv is not None else 0

            return Pair(
                API.DEXSC,
                pair_dict.get("chainId"),
                pair_dict.get("dexId"),
                pair_dict.get("url"),
                pair_dict.get("pairAddress"),
                base_token,
                quote_token,
                pair_dict["priceNative"],
                txns,
                volume,
                price_change,
                pair_dict.get("labels") or [],
                pair_dict.get("priceUsd"),
                liquidity,
                fdv,
                pair_dict.get("telegram"),
                pair_dict.get("twitter"),
                pair_dict.get("website"),
            )
        except Exception as e:
            print(f"from_dexsc_dict: {e}")

    @staticmethod
    def from_gecko_dict(data: dict):
        relationships = data["relationships"]
        base_token_data = relationships["base_token"]["data"]
        quote_token_data = relationships["quote_token"]["data"]
        dex = relationships["dex"]["data"]["id"].split("_")
        dexId = dex[0]
        labels = dex[1] if len(dex) > 1 else []
        attrs = data["attributes"]
        symbols = attrs["name"].split(" / ")
        liquidity = float(attrs["reserve_in_usd"])
        base_token_address = base_token_data["id"].split("_")[1]
        base_token = Token(
            base_token_address,
            symbols[0],
            symbols[0],
        )
        quote_token = Token(
            quote_token_data["id"].split("_")[1],
            symbols[1],
            symbols[1],
        )

        # txns_data = attrs["transactions"]
        # txns = {
        #     "h1": Transaction(
        #         int(txns_data["h1"]["buys"]), int(txns_data["h1"]["sells"])
        #     ),
        #     "h24": Transaction(
        #         int(txns_data["h24"]["buys"]), int(txns_data["h24"]["sells"])
        #     ),
        # }
        txns = None
        pairAddress = attrs["address"]

        # volume_data = attrs["volume_usd"]
        # volume = Volume(float(volume_data["h1"]), float(volume_data["h24"]))
        volume = None

        price_change_data = attrs["price_change_percentage"]
        price_change = PriceChange(
            float(price_change_data["h1"]), float(price_change_data["h24"])
        )
        chainId = data["id"].split("_")[0]
        url = f"https://www.geckoterminal.com/{chainId}/pools/{pairAddress}"
        return Pair(
            API.GECKO,
            chainId,
            dexId,
            url,
            pairAddress,
            base_token,
            quote_token,
            float(attrs["base_token_price_quote_token"]),
            txns,
            volume,
            price_change,
            labels,
            float(attrs.get("base_token_price_usd")),
            liquidity,
            float(attrs.get("fdv_usd")),
        )

    def to_dict(self) -> Dict:
        pair_dict = {
            "api": self.api,
            "chainId": self.chainId,
            "dexId": self.dexId,
            "url": self.url,
            "pairAddress": self.pairAddress,
            "baseToken": {
                "address": self.baseToken.address,
                "name": self.baseToken.name,
                "symbol": self.baseToken.symbol,
            },
            "quoteToken": {
                "address": self.quoteToken.address,
                "name": self.quoteToken.name,
                "symbol": self.quoteToken.symbol,
            },
            # "priceNative": self.priceNative,
            # "txns": (
            #     {
            #         key: {"buys": value.buys, "sells": value.sells}
            #         for key, value in self.txns.items()
            #     }
            #     if self.txns
            #     else None
            # ),
            # "volume": {
            #     "h1": self.volume.h1,
            #     "h24": self.volume.h24,
            # },
            # "priceChange": {
            #     "h1": self.priceChange.h1,
            #     "h24": self.priceChange.h24,
            # },
            "labels": self.labels,
            "priceUsd": self.priceUsd,
            "fdv": self.fdv,
            "liquidity": self.liquidity,
            "telegram": self.telegram,
            "twitter": self.twitter,
            "website": self.website,
        }
        return pair_dict


class DEXScreener:
    async def get_pair_by_token(
        token_address: str, chain_id: str, dex_id: str = None, ver: str = None
    ):
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(response.status)

                    data = await response.json()
                    if not data["pairs"]:
                        return None
                    for pair in data["pairs"]:
                        if (
                            pair["chainId"] == chain_id
                            and (dex_id is None or pair.get("dexId") == dex_id)
                            and (ver is None or ver in pair.get("labels", []))
                        ):
                            return Pair.from_dexsc_dict(pair)
        except Exception as err:
            print(f"failed to get pair by token address from dexscreener: {err}")

    async def get_pair_by_pairAddress(pair_address: str, chain_id: str):
        url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(response.status)
                    data = await response.json()
                    if not data["pairs"]:
                        return None
                    for pair in data["pairs"]:
                        if pair["pairAddress"].lower() == pair_address.lower():
                            return Pair.from_dexsc_dict(pair)

        except Exception as err:
            print(f"failed to get pair address from dexscreener: {err}")

    async def search_address(token_address: str):
        url = f"https://api.dexscreener.com/latest/dex/search/?q={token_address}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(response.status)
                    data = await response.json()
                    if not data["pairs"]:
                        return None
                    pairs: List[Pair] = []
                    for pair in data["pairs"]:
                        try:
                            pairs.append(Pair.from_dexsc_dict(pair))
                        except:
                            pass
                    return pairs
        except Exception as err:
            print(f"failed to search address from dexscreener: {err}")
