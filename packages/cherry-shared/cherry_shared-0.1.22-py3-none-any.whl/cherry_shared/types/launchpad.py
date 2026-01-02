class LaunchpadToken:
    def __init__(
        self,
        token_address: str,
        decimals: str,
        total_supply: str,
        token_name: str,
        token_symbol: str,
        chain: str,
        pair_address: str,
        telegram: str,
        twitter: str,
        website: str,
    ):
        self.token_address = token_address
        self.decimals = int(decimals)
        self.total_supply = int(float(total_supply))
        self.token_name = token_name
        self.token_symbol = token_symbol
        self.chain = chain
        self.pair_address = pair_address
        self.telegram = telegram
        self.twitter = twitter
        self.website = website

    @staticmethod
    def create_token_info(data_dict):
        # Defensive copy to avoid mutating input
        data = dict(data_dict) if data_dict else {}

        # Handle totalSupply safely
        total_supply = data.get("totalSupply", 0)
        try:
            if str(total_supply).lower() == "nan":
                total_supply = 0
            total_supply = int(float(total_supply))
        except (ValueError, TypeError):
            total_supply = 0

        # Handle decimals safely
        decimals = data.get("decimals", 0)
        try:
            decimals = int(decimals)
        except (ValueError, TypeError):
            decimals = 0

        return LaunchpadToken(
            token_address=data.get("tokenAddress", ""),
            decimals=decimals,
            total_supply=total_supply,
            token_name=data.get("name", ""),
            token_symbol=data.get("symbol", ""),
            chain=data.get("chain", ""),
            pair_address=data.get("pairAddress", ""),
            telegram=data.get("telegram", ""),
            twitter=data.get("twitter", ""),
            website=data.get("website", ""),
        )

    def to_dict(self):
        return {
            "tokenAddress": self.token_address,
            "decimals": self.decimals,
            "totalSupply": self.total_supply,
            "name": self.token_name,
            "symbol": self.token_symbol,
            "chain": self.chain,
            "pairAddress": self.pair_address,
            "telegram": self.telegram,
            "twitter": self.twitter,
            "website": self.website,
        }
