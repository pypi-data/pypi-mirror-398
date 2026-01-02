class UserWallet:
    def __init__(self, user_id: int, address: str, pk: str, chain: str):
        self.user_id = user_id
        self.address = address
        self.pk = pk
        self.chain = chain

    def __repr__(self):
        return f"Wallet(user_id={self.user_id}, address={self.address}, pk={self.pk}, chain={self.chain})"
