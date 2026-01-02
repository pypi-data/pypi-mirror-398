class LeaderboardEntry:
    def __init__(
        self,
        chat_id: int,
        chat_name: str = None,
        chat_link: str = None,
        token_link: str = None,
        boosted_score: int = 0,
        raid_score: int = 0,
    ):
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.chat_link = chat_link
        self.token_link = token_link
        self.boosted_score = boosted_score
        self.raid_score = raid_score

    @property
    def boosted(self):
        return self.boosted_score > 0

    @boosted.setter
    def boosted(self, value):
        pass  # Prevent setting boosted directly

    @property
    def score(self):
        return int((self.boosted_score or 0) + (self.raid_score or 0))

    @score.setter
    def score(self, value):
        pass  # Prevent setting score directly

    def to_dict(self):
        return {
            "chat_id": str(self.chat_id),
            "chat_name": self.chat_name,
            "chat_link": self.chat_link,
            "token_link": self.token_link,
            "boosted": int(self.boosted),
            "score": str(self.score),
            "boosted_score": (str(int(self.boosted_score or 0))),
            "raid_score": (str(int(self.raid_score or 0))),
        }

    def __repr__(self):
        return (
            f"LeaderboardEntry(chat_id={self.chat_id}, chat_name={self.chat_name}, "
            f"chat_link={self.chat_link}, token_link={self.token_link}, score={self.score}), boosted={self.boosted}, "
            f"boosted_score={self.boosted_score}, raid_score={self.raid_score})"
        )

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            chat_id=int(data.get("chat_id")),
            chat_name=data.get("chat_name"),
            chat_link=data.get("chat_link"),
            token_link=data.get("token_link"),
            boosted_score=int(data.get("boosted_score", 0)),
            raid_score=int(data.get("raid_score", 0)),
        )
