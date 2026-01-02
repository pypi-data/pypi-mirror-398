class PostInfo:
    def __init__(
        self, link: str, likes: int, comments: int, shares: int = 0, bookmarks: int = 0
    ):
        self.link = link
        self.likes = likes
        self.shares = shares
        self.comments = comments
        self.bookmarks = bookmarks

    def __str__(self):
        return (
            f"{self.link},{self.likes},{self.comments},{self.shares},{self.bookmarks}"
        )

    def __repr__(self):
        return self.__str__()

    def log(self):
        return f"Post info likes={self.likes}, comments={self.comments}, shares={self.shares}, bookmarks={self.bookmarks}"

    @classmethod
    def from_string(cls, string: str):
        parts = string.split(",")
        link = parts[0] if parts[0] != "None" else None
        likes, shares, comments, bookmarks = map(int, parts[1:])
        return cls(link, likes, shares, comments, bookmarks)


class RaidInfo:
    def __init__(
        self,
        post: PostInfo,
        started_by: int,
        bounty: float,
        message_id: int,
        lock: bool = False,
        platform: str = None,
        bounty_type: int = None,
    ):
        self.post = post
        self.started_by = started_by
        self.bounty = bounty
        self.message_id = message_id
        self.lock = lock
        self.platform = platform
        self.bounty_type = bounty_type

    def make(
        started_by: int,
        message_id: int,
        link: str = None,
        likes: int = 0,
        shares: int = 0,
        comments: int = 0,
        bookmarks: int = 0,
        bounty: float = 0,
        lock: bool = False,
        platform: str = None,
        bounty_type: int = None,
    ):
        post = PostInfo(link, likes, comments, shares, bookmarks)
        return RaidInfo(
            post, started_by, bounty, message_id, lock, platform, bounty_type
        )

    def __str__(self):
        return f"{str(self.post)}|{self.started_by},{self.bounty},{self.message_id},{int(self.lock)},{self.platform},{self.bounty_type}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string: str):

        post_string, raid_string = string.split("|")
        parts = raid_string.split(",")
        started_by = int(parts[0])
        bounty = float(parts[1])
        message_id = int(parts[2])
        lock = bool(int(parts[3]))
        platform = parts[4] if parts[4] != "None" else None
        bounty_type = int(parts[5]) if parts[5] != "None" else None
        post = PostInfo.from_string(post_string)
        return cls(post, started_by, bounty, message_id, lock, platform, bounty_type)

    def log(self) -> str:
        return (
            f"Raid info: started_by={self.started_by}, bounty={self.bounty}, "
            f"message_id={self.message_id}, bounty_type={self.bounty_type}, "
            f"lock={self.lock}, platform={self.platform}, post={self.post.log()}"
        )
