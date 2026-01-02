from enum import Enum
from typing import List, Union
from cherry_shared.blockchains import ChainType
from cherry_shared.constants import Constants


class LaunchPadId(Enum):
    PINKSALE = "pinksale"
    FJORD = "fjord"
    SOLPAD = "solpad"
    PUMPFUN = "pumpfun"
    LetsBonk = "letsbonk"
    MOONSHOT = "moonshot"
    SUNPUMP = "sunpump"
    FOURMEME = "fourmeme"
    ETHERVISTA = "ethervista"
    MOVEPUMP = "movepump"
    BOOPFUN = "boopfun"

    @staticmethod
    def all():
        return [
            LaunchPadId.PUMPFUN,
            # LaunchPadId.FJORD,
            # LaunchPadId.SOLPAD,
            # LaunchPadId.LetsBonk,
            # LaunchPadId.MOONSHOT,
            # LaunchPadId.SUNPUMP,
            # LaunchPadId.FOURMEME,
            # LaunchPadId.ETHERVISTA,
            # LaunchPadId.MOVEPUMP,
            # LaunchPadId.BOOPFUN,
        ]


class LaunchPad:
    def __init__(
        self,
        id: LaunchPadId,
        group: int,
        name: str,
        website: str,
        info_route: str,
        supported_chains: List[ChainType],
        trending_channel: str,
    ):
        self.id = id
        self.group = group
        self.name = name
        self.website = website
        self.info_route = info_route
        self.supported_chains = supported_chains
        self.trending_channel = trending_channel


class LaunchPads:
    # GROUP 1
    pumpfun = LaunchPad(
        LaunchPadId.PUMPFUN,
        1,
        "Pump.fun",
        "https://pump.fun",
        "pumpfun",
        [ChainType.SOLANA],
        "https://t.me/pumpfuncherry",
    )
    letsbonk = LaunchPad(
        LaunchPadId.LetsBonk,
        1,
        "LetsBonk",
        "https://letsbonk.com",
        "letsbonk",
        [ChainType.SOLANA],
        Constants.trending_channel_link,
    )
    moonshot = LaunchPad(
        LaunchPadId.MOONSHOT,
        1,
        "MoonShot",
        "https://dexscreener.com/moonshot",
        "moonshot",
        [ChainType.SOLANA],
        "https://t.me/moonshotcherry",
    )
    sunpump = LaunchPad(
        LaunchPadId.SUNPUMP,
        1,
        "SunPump",
        "https://sunpump.meme",
        "sunpump",
        [ChainType.TRON],
        "https://t.me/sunpumptrendingcherry",
    )
    fourmeme = LaunchPad(
        LaunchPadId.FOURMEME,
        1,
        "Four.Meme",
        "https://four.meme",
        "fourmemes",
        [ChainType.EVM],
        Constants.trending_channel_link,
    )
    ethervista = LaunchPad(
        LaunchPadId.ETHERVISTA,
        1,
        "Ether Vista",
        "https://ethervista.app",
        "ethervista",
        [ChainType.EVM],
        Constants.trending_channel_link,
    )

    movepump = LaunchPad(
        LaunchPadId.MOVEPUMP,
        1,
        "Move Pump",
        "https://movepump.com",
        "movepump",
        [ChainType.SUI],
        Constants.trending_channel_link,
    )

    boopfun = LaunchPad(
        LaunchPadId.BOOPFUN,
        1,
        "Boop.Fun",
        "https://boop.fun",
        "boopfun",
        [ChainType.SOLANA],
        Constants.trending_channel_link,
    )

    # GROUP 2
    pinksale = LaunchPad(
        LaunchPadId.PINKSALE,
        2,
        "PinkSale",
        "https://www.pinksale.finance",
        "pink",
        [ChainType.EVM, ChainType.SOLANA],
        Constants.trending_channel_link,
    )
    fjord = LaunchPad(
        LaunchPadId.FJORD,
        2,
        "FJORD Sale",
        "https://app.fjordfoundry.com",
        "fjord",
        [ChainType.EVM],
        Constants.trending_channel_link,
    )
    solpad = LaunchPad(
        LaunchPadId.SOLPAD,
        2,
        "SolPad",
        "https://solpad.io",
        "solpad",
        [ChainType.SOLANA],
        Constants.trending_channel_link,
    )

    @staticmethod
    def all() -> List[LaunchPad]:
        return [
            LaunchPads.pumpfun,
            # LaunchPads.letsbonk,
            # LaunchPads.moonshot,
            # LaunchPads.sunpump,
            # LaunchPads.fourmeme,
            # LaunchPads.ethervista,
            # LaunchPads.boopfun,
            # LaunchPads.movepump,
            # LaunchPads.pinksale,
            # LaunchPads.fjord,
            # LaunchPads.solpad,
        ]

    @staticmethod
    def get_by_id(id: Union[LaunchPadId | str]) -> LaunchPad:
        if isinstance(id, str):
            id = LaunchPadId(id)

        for lp in LaunchPads.all():
            if lp.id == id:
                return lp

    @staticmethod
    def get_group(group_id: int):
        return [lp for lp in LaunchPads.all() if lp.group == group_id]

    @staticmethod
    def get_by_chain_type(chainType: ChainType):
        return [l for l in LaunchPads.all() if chainType in l.supported_chains]
