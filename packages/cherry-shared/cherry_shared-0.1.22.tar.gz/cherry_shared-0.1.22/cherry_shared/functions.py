from datetime import datetime, timedelta
import hashlib
import json
import random
import re
import string
import time
from typing import Optional, Union
from pyrogram.types import Message, Photo, Video, Document, VideoNote, Animation, Audio
from itertools import zip_longest
from cherry_shared.emojis import Emojis
from web3 import Web3


def extract_arguments(text: str) -> str:
    """
    Returns the argument after the command.
    :param text: String to extract the arguments from a command
    :return: the arguments if `text` is a command (according to is_command), else None.
    """
    regexp = re.compile(r"/\w*(@\w*)*\s*([\s\S]*)", re.IGNORECASE)
    result = regexp.match(text)
    return result.group(2) if is_command(text) else None


def extract_entities(entities: list, start: int, len: int) -> list:
    """
    Returns the entities of a Message Object.
    :param entities: list of MessageEntity
    :param start: start index of the reduced text
    :param len: length of the reduced text
    :return: list of new reduced MessageEntity
    """
    if not entities:
        return []
    new_entities = []
    for entity in entities:
        if entity.offset < start:
            continue
        if entity.offset + entity.length > start + len:
            continue
        entity.offset -= start
        new_entities.append(entity)
    return new_entities


def is_command(text: str) -> bool:
    """
    Checks if `text` is a command. Telegram chat commands start with the '/' character.

    :param text: Text to check.
    :return: True if `text` is a command, else False.
    """
    if not text:
        return False
    return text.startswith("/")


url_pattern = re.compile(
    r"(?<!\S)(?:https?://)"  # Scheme with negative lookbehind
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # Domain
    r"localhost|"  # Localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
    r"(?::\d+)?"  # Port (optional)
    r"(?:/?|[/?]\S*?)(?=[\s\]\"']|$)",  # Path (non-greedy) with lookahead for space, closing bracket, quote, or end of string
    re.IGNORECASE,
)


def get_url_from_text(text: str):
    try:
        matches = url_pattern.findall(text)
        if matches:
            return matches[0]
    except Exception as e:
        return None


def get_file_id(message: Message):
    """Returns file_id of media message"""
    media = get_media(message)
    if media:
        return media.file_id
    return None


def get_media(
    m: Message,
) -> Optional[Union[Photo, Video, Document, Audio, VideoNote, Animation]]:
    """Returns file_id of media message"""
    if not m.media:
        return None
    media = str(m.media).lower().split(".")[1]
    if media in ("photo", "video", "audio", "document", "video_note", "animation"):
        return getattr(m, media, None)
    return None


def smart_split(text: str, chars_per_string: int = 4096) -> list[str]:
    r"""
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.
    If `chars_per_string` > 4096: `chars_per_string` = 4096.
    Splits by '\n', '. ' or ' ' in exactly this priority.
    :param text: The text to split
    :type text: :obj:`str`
    :param chars_per_string: The number of maximum characters per part the text is split to.
    :type chars_per_string: :obj:`int`
    :return: The splitted text as a list of strings.
    :rtype: :obj:`list` of :obj:`str`
    """

    def _text_before_last(substr: str) -> str:
        return substr.join(part.split(substr)[:-1]) + substr

    if chars_per_string > chars_per_string:
        chars_per_string = chars_per_string

    parts = []
    while True:
        if len(text) < chars_per_string:
            parts.append(text)
            return parts

        part = text[:chars_per_string]

        if "\n" in part:
            part = _text_before_last("\n")
        elif ". " in part:
            part = _text_before_last(". ")
        elif " " in part:
            part = _text_before_last(" ")

        parts.append(part)
        text = text[len(part) :]


class Address:  # TODO: Must find address in text not match it
    _base58_pattern = re.compile(r"^[1-9A-HJ-NP-Za-km-zA-L]{43,44}$")
    _sei_pattern = re.compile(r"^sei1[a-z0-9]{58}$")
    _evm_address_pattern = re.compile(r"0x[a-fA-F0-9]{40}")
    _evm_txHash_pattern = re.compile(r"0x[a-fA-F0-9]{66}")
    _trx_address_pattern = re.compile(r"T[1-9A-HJ-NP-Za-km-z]{33}")
    _ton_address_pattern = re.compile(r"^[A-Za-z0-9_-]{48}$")
    _sui_address_pattern = re.compile(r"^(0x[a-fA-F0-9]{64}|[A-Za-z0-9_-]{48})$")
    _sui_address_module = re.compile(
        r"^0x[a-fA-F0-9]{64}::[a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*$"
    )

    def __init__(self, chain: str, address: str) -> None:
        self.chain = chain
        self.address = address

    @classmethod
    def is_solana_address(cls, address: str):
        return cls._base58_pattern.match(address)

    @classmethod
    def is_sei_contract_address(cls, address: str):
        return cls._sei_pattern.match(address)

    @classmethod
    def is_evm_address(cls, text: str):
        return cls._evm_address_pattern.match(text)

    @classmethod
    def is_tx_hash(cls, text: str):
        return re.match(cls._evm_txHash_pattern, text)

    @classmethod
    def is_trx_address(cls, text: str):
        return cls._trx_address_pattern.match(text)

    @classmethod
    def is_ton_address(cls, text: str):
        return cls._ton_address_pattern.match(text)

    @classmethod
    def is_sui_address(cls, text: str):
        return cls._sui_address_pattern.match(text) or cls._sui_address_module.match(
            text
        )

    @classmethod
    def detect(cls, address: str):
        if address.startswith("0x"):
            sui = cls.is_sui_address(address)
            if sui:
                address = sui.group(0)
                return cls("sui", address)

            eth = cls.is_evm_address(address)
            if eth:
                address = eth.group(0)
                checksum = Web3.to_checksum_address(address)
                return cls("evm", checksum)

        elif address.startswith("sei"):
            sei = cls.is_sei_contract_address(address)
            if sei:
                return cls("sei-network", sei.group(0))
        else:
            sol = cls.is_solana_address(address)
            if sol:
                return cls("solana", sol.group(0))

            trx = cls.is_trx_address(address)
            if trx:
                return cls("tron", trx.group(0))

    def __str__(self):
        return f"Address({self.address}, {self.chain})"


def generate_promo_code(user_id: int, code_length: int = 5):
    byte_string = str(user_id).encode()
    hash = hashlib.sha256(byte_string).hexdigest()
    seed = int(hash[:8], 16)
    random.seed(seed)
    code_chars = string.ascii_uppercase + string.digits
    promo_code = "".join(random.choice(code_chars) for _ in range(code_length))
    return promo_code


def generate_random_promo_code(code_length: int = 5):
    """
    Generate a single random promo code.

    Args:
        code_length (int, optional): The length of the promo code. Defaults to 8.

    Returns:
        str: A randomly generated promo code.
    """
    code_chars = string.ascii_uppercase + string.digits
    promo_code = "".join(random.choice(code_chars) for _ in range(code_length))
    return promo_code


def format_number(value, f_points=1):
    if value < 1000:
        return f"{value:.{f_points}f}"
    elif value < 1000000:
        return f"{value / 1000:.{f_points}f}K"
    elif value < 1000000000:
        return f"{value / 1000000:.{f_points}f}M"
    else:
        return f"{value / 1000000000:.{f_points}f}B"


def time_difference(dt: datetime):
    now_utc = datetime.utcnow()
    diff = dt - now_utc
    total_seconds = int(diff.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 0:
        return f"{hours} hours and {minutes} minutes"
    else:
        return f"{minutes} minutes"


def contains_text(text1: str, text2: str) -> bool:
    """
    Check if text1 is present in text2, ignoring case.

    :param text1: The first string to compare.
    :param text2: The second string to compare.
    :return: True if text1 is present in text2, False otherwise.
    """
    pattern = re.compile(re.escape(text1), re.IGNORECASE)
    return pattern.search(text2) is not None


def truncate_text(text: str, max_length: int) -> str:
    if not text:
        return None
    if len(text) > max_length:
        return text[: max_length - 2] + ".."
    else:
        return text


def estimate_async_runtime(func):
    async def wrapper(*args, **kwargs):
        start_time = time.process_time_ns()
        result = await func(*args, **kwargs)
        end_time = time.process_time_ns()
        runtime = (end_time - start_time) / 1_000_000
        print(f"Estimated runtime of {func.__name__}: {runtime:.2f} ms")
        return result

    return wrapper


def estimate_sync_runtime(func):
    def wrapper(*args, **kwargs):
        start_time = time.process_time_ns()
        result = func(*args, **kwargs)
        end_time = time.process_time_ns()
        runtime = (end_time - start_time) / 1_000_000
        print(f"Estimated runtime of {func.__name__}: {runtime:.2f} ms")
        return result

    return wrapper


def create_progress_bar(current_progress, max_length=12):
    filled_blocks = round(current_progress / 100 * max_length)

    # Ensure the bar is not completely green unless the progress is 100%
    if filled_blocks == max_length and current_progress < 100:
        filled_blocks -= 1

    empty_blocks = max_length - filled_blocks
    progress_bar = "".join(["🟩"] * filled_blocks + ["⬛️"] * empty_blocks)

    return progress_bar


def animated_progress_bar(current_progress: int, max_length=10):

    filled_blocks = round(current_progress / 100 * max_length)

    # Ensure the bar is not completely green unless the progress is 100%
    if filled_blocks == max_length and current_progress < 100:
        filled_blocks -= 1

    empty_blocks = max_length - filled_blocks

    progress_bar = [Emojis.progress_bar.mid_full] * filled_blocks + [
        Emojis.progress_bar.mid_empty
    ] * empty_blocks

    # Replace the first block
    if progress_bar[0] == Emojis.progress_bar.mid_full:
        progress_bar[0] = Emojis.progress_bar.start_full
    else:
        progress_bar[0] = Emojis.progress_bar.start_empty

    # Replace the last block
    if progress_bar[-1] == Emojis.progress_bar.mid_full:
        progress_bar[-1] = Emojis.progress_bar.end_full
    else:
        progress_bar[-1] = Emojis.progress_bar.end_empty

    progress_bar = "".join(progress_bar)
    return progress_bar


def get_elapsed_time_str(start: float, show_seconds: bool = False) -> str:
    """
    Get the elapsed time since a given start time.

    Parameters:
    - start (float): The start time, as returned by time.time().

    Returns:
    - str: The elapsed time, in the format "Xh Ym Zs", but without hours and minutes if their value is 0.
    """
    elapsed_seconds = int(time.time() - start)
    if elapsed_seconds < 1:
        return "a few moments"
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        if show_seconds:
            parts.append(f"{seconds}s")
        elif not show_seconds and minutes + hours == 0:
            parts.append("a few seconds")
    return " ".join(parts)


def get_elapsed_time_full(
    start: float = None, seconds: int = None, show_seconds: bool = False
) -> str:
    """
    Get the elapsed time since a given start time, in full words.

    Parameters:
    - start (float): The start time, as returned by time.time()..
    - seconds (int): estimated seconds.

    Returns:
    - str: The elapsed time, in the format "X hours Y minutes Z seconds", but without hours and minutes if their value is 0, and with singular/plural forms.
    """
    elapsed_seconds = int(time.time() - start) if start else seconds
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, reminded_seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if reminded_seconds > 0:
        if show_seconds:
            parts.append(
                f"{reminded_seconds} second{'s' if reminded_seconds != 1 else ''}"
            )
        elif hours + minutes == 0:
            parts.append(f"a few moments")

    return " and ".join(parts)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    args = [iter(iterable)] * n
    return [list(filter(None, i)) for i in zip_longest(*args, fillvalue=fillvalue)]


def get_str_time_full(seconds: float, show_seconds: bool = False) -> str:
    try:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if hours > 0:
            parts.append(f"{int(hours)} Hour{'s' if int(hours) != 1 else ''}")
        if minutes > 0:
            parts.append(f"{int(minutes)} Minute{'s' if int(minutes) != 1 else ''}")
        if seconds > 0:
            parts.append(f"{int(seconds)} Second{'s' if int(seconds)!=1 else ''}")
        if not parts:
            return "0 seconds"
        return " and ".join(parts)
    except Exception as e:
        print(f"get_str_time_full: {e}")
        return "0 seconds"


def get_str_time_full2(
    start: float = None, seconds: int = None, show_seconds: bool = False
) -> str:
    """
    Get the elapsed time since a given start time, in full words.

    Parameters:
    - start (float): The start time, as returned by time.time().
    - seconds (int): estimated seconds.

    Returns:
    - str: The elapsed time, in the format "X hours Y minutes Z seconds", but without hours and minutes if their value is 0, and with singular/plural forms.
    """
    elapsed_seconds = int(time.time() - start) if start else seconds
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, reminded_seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if reminded_seconds > 0:
        if show_seconds:
            parts.append(
                f"{reminded_seconds} second{'s' if reminded_seconds != 1 else ''}"
            )
        elif hours + minutes == 0:
            parts.append(f"a few moments")

    return " and ".join(parts)


def time_ago_str(event_timestamp):
    current_time = time.time()
    time_difference = datetime.fromtimestamp(current_time) - datetime.fromtimestamp(
        event_timestamp
    )

    days_ago = time_difference.days
    seconds_ago = time_difference.seconds

    if days_ago == 0:
        hours_ago = seconds_ago // 3600
        if hours_ago > 0:
            return f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"

        minutes_ago = seconds_ago // 60
        if minutes_ago > 0:
            return f"{minutes_ago} minute{'s' if minutes_ago > 1 else ''} ago"

        return "just now"

    if days_ago < 7:
        return f"{days_ago} day{'s' if days_ago > 1 else ''} ago"

    weeks_ago = days_ago // 7
    if days_ago < 30:
        return f"{weeks_ago} week{'s' if weeks_ago > 1 else ''} ago"

    months_ago = days_ago // 30
    return f"{months_ago} month{'s' if months_ago > 1 else ''} ago"


def seconds_until_next_minute_mod_5():
    now = datetime.now()
    minutes_to_add = (5 - now.minute % 5) % 5
    next_time = (now + timedelta(minutes=minutes_to_add)).replace(
        second=0, microsecond=0
    )

    # If we're within a minute divisible by 5 but not at the exact start, move to the next 5-minute mark
    if now.minute % 5 == 0 and now.second > 0:
        next_time += timedelta(minutes=5)

    return (next_time - now).total_seconds()
