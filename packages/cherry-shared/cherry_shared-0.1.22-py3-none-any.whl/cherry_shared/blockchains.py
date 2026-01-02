from typing import Dict, List, Set
from cherry_shared.types.blockchain import Blockchain, SupportedFeatures
from functools import lru_cache
from enum import Enum


class ChainType(Enum):
    EVM = "evm"
    SOLANA = "solana"
    TRON = "tron"
    TON = "ton"
    SUI = "sui"


class BlockchainId:
    SOL = "solana"
    ETH = "ethereum"
    BSC = "bsc"
    TRX = "tron"
    BASE = "base"
    SUI = "sui"
    MANTA = "manta"
    MATIC = "polygon"
    XPL = "plasma"


class Blockchains:
    SOL = Blockchain(
        BlockchainId.SOL,
        "SOL",
        "Solana",
        "SOL",
        "https://solscan.io/token",
        False,
        {
            3: {3: 0, 6: 0, 12: 6, 24: 9},
            10: {3: 1.6 , 6: 2.5, 12: 4, 24: 6},
        },
        ["SOL", "USDC"],
        {
            150: 0.2,
            300: 0.4,
        },
        SupportedFeatures(custom_token=True, wallet=True, payment=True),
        0.1,
        extras={
            "volume_price": {
             50000: 3.2,
             100_000: 5.8,
             250_000: 13.0,
             500_000: 24.6,
             1_000_000: 45.8,
             5_000_000: 214.6,
            },
            "holders_price": {
                1000: 2.2,
                2500: 5.5,
                5000: 11,
                10000: 22,
                25000: 55,
                100_000: 220,
            },
            "boost_price": {1000: 0.4, 2000: 0.7, 4000: 1.3, 8000: 2.5},
        },
    )

    ETH = Blockchain(
        BlockchainId.ETH,
        "ETH",
        "Ethereum",
        "ETH",
        "https://etherscan.io/token",
        True,
        {
            3: {3: 0.2, 6: 0.4, 12: 0.6, 24: 0.9},
            10: {3: 0.1, 6: 0.2, 12: 0.4, 24: 0.6},
        },
        ["WETH", "USDT", "USDC"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=True, wallet=True, payment=True),
        0.05,
    )

    BSC = Blockchain(
        BlockchainId.BSC,
        "BSC",
        "Binance Smart Chain",
        "BNB",
        "https://bscscan.com/token",
        True,
        {
            3: {3: 0.7, 6: 1.2, 12: 2.0, 24: 3.5},
            10: {3: 0.6, 6: 0.8, 12: 1.5, 24: 2.5},
        },
        ["WBNB", "USDT", "USDC"],
        {150: 0.1, 300: 0.2, 950: 0.5, 2500: 1},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        0.1,
        extras={
            "boost_price": {1000: 0.7, 2000: 1.4, 4000: 2.5, 8000: 4.6},
        },
    )

    TRX = Blockchain(
        BlockchainId.TRX,
        "TRX",
        "Tron",
        "TRX",
        "https://tronscan.org/#/token20",
        False,
        {
            3: {3: 1260, 6: 2270, 12: 3530, 24: 6050},
            10: {3: 1000, 6: 1770, 12: 3020, 24: 4540},
        },
        ["WTRX", "USDT", "USDC"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        10,
    )

    BASE = Blockchain(
        BlockchainId.BASE,
        "BASE",
        "Base",
        "ETH",
        "https://basescan.org/token",
        True,
        {
            3: {3: 0.2, 6: 0.4, 12: 0.6, 24: 0.9},
            10: {3: 0.1, 6: 0.2, 12: 0.4, 24: 0.6},
        },
        ["WETH", "USDT", "USDC"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        0.1,
    )

    MATIC = Blockchain(
        BlockchainId.MATIC,
        "POL",
        "Polygon",
        "POL",
        "https://polygonscan.com/token",
        True,
        {
            3: {3: 800, 6: 1330, 12: 2100, 24: 3430},
            10: {3: 520, 6: 800, 12: 1330, 24: 2100},
        },
        ["WPOL", "USDT", "USDC"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        10,
    )

    MANTA = Blockchain(
        BlockchainId.MANTA,
        "MANTA",
        "MANTA",
        "ETH",
        "https://pacific-explorer.manta.network/token",
        True,
        {
            3: {3: 0.2, 6: 0.4, 12: 0.6, 24: 0.9},
            10: {3: 0.1, 6: 0.2, 12: 0.4, 24: 0.6},
        },
        ["WETH", "USDT", "USDC", "MANTA"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        0.05,
    )

    SUI = Blockchain(
        "sui",
        "SUI",
        "SUI Network",
        "SUI",
        "https://suiscan.xyz/mainnet/coin",
        False,
        {
            3: {3: 170, 6: 295, 12: 505, 24: 845},
            10: {3: 125, 6: 230, 12: 395, 24: 675},
        },
        ["SUI", "USDC"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        10,
    )

    XPL = Blockchain(
        "plasma",
        "XPL",
        "Plasma",
        "XPL",
        "https://plasmascan.to/token",
        True,
        {
            3: {3: 518, 6: 951, 12: 1677, 24: 2715},
            10: {3: 415, 6: 726, 12: 1487, 24: 1989},
        },
        ["WXPL", "USDT0", "USDC", "XPL"],
        {150: 0.02, 300: 0.04, 950: 0.1, 2500: 0.2},
        SupportedFeatures(custom_token=False, wallet=True, payment=True),
        10,
    )

    @staticmethod
    @lru_cache()
    def dict() -> Dict[str, Blockchain]:
        return {
            BlockchainId.SOL: Blockchains.SOL,
            BlockchainId.ETH: Blockchains.ETH,
            BlockchainId.BSC: Blockchains.BSC,
            BlockchainId.TRX: Blockchains.TRX,
            BlockchainId.BASE: Blockchains.BASE,
            BlockchainId.SUI: Blockchains.SUI,
            BlockchainId.MANTA: Blockchains.MANTA,
            BlockchainId.MATIC: Blockchains.MATIC,
            BlockchainId.XPL: Blockchains.XPL,
        }

    @staticmethod
    def all() -> List[Blockchain]:
        return Blockchains.dict().values()

    @lru_cache()
    def get_by_id(id: str) -> Blockchain:
        """Retrieve a blockchain by its ID."""
        return Blockchains.dict().get(id)

    @lru_cache()
    def get_all_ids() -> List[str]:
        """Return a list of all blockchain IDs."""
        return Blockchains.dict().keys()

    @lru_cache()
    def all_chain_types() -> Set[str]:
        """Return a list of all blockchain IDs."""
        types = {c.chain_type for c in Blockchains.all()}
        return types

    @lru_cache()
    def evms() -> List[Blockchain]:
        """Retrieve all EVM-compatible blockchains."""
        return [chain for chain in Blockchains.all() if chain.evm]

    @staticmethod
    @lru_cache()
    def get_by_chain_type(chain_type: str) -> List[Blockchain]:
        return [chain for chain in Blockchains.all() if chain.chain_type == chain_type]

    @staticmethod
    @lru_cache()
    def get_chain_symbols() -> List[str]:
        return [c.symbol for c in Blockchains.all()]

    @staticmethod
    @lru_cache()
    def get_active_wallet_chains() -> List[str]:
        chain_types = Blockchains.all_chain_types()
        active_chain_types = []
        for chain_type in chain_types:
            chain = Blockchains.get_by_chain_type(chain_type)[0]
            if chain and chain.supported_features.wallet:
                active_chain_types.append(chain_type)
        return active_chain_types
