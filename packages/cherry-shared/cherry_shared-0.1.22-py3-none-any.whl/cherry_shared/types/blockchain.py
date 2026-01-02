from typing import Any, Dict, List


class SupportedFeatures:
    def __init__(self, custom_token: bool, wallet: bool, payment: bool):
        self.custom_token = custom_token
        self.wallet = wallet
        self.payment = payment

    def __repr__(self):
        return (
            f"SupportedFeatures(custom_token={self.custom_token}, wallet={self.wallet}, "
            f"trend={self.payment})"
        )


class Blockchain:
    def __init__(
        self,
        id: str,
        symbol: str,
        name: str,
        native_token: str,
        explorer: str,
        evm: bool,
        trending_prices: Dict[str, Dict[int, float]],
        quote_tokens: List[str],
        boost_price: Dict[int, float],
        supported_features: SupportedFeatures,
        min_bounty: float = 0.0,
        extras: Dict[str, Any] = {}
    ):
        self.id = id
        self.symbol = symbol
        self.name = name
        self.native_token = native_token
        self.explorer = explorer
        self.evm = evm
        self.min_bounty = min_bounty
        self.trending_prices = trending_prices
        self.quote_tokens = quote_tokens
        self.boost_price = boost_price
        self.supported_features = supported_features
        self.extras = extras.copy()

    @property
    def chain_type(self):
        return "evm" if self.evm else self.id

    def __repr__(self):
        return f"{self.name}"
