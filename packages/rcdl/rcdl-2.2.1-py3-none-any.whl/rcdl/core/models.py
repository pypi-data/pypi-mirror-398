# core/models.py

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class VideoStatus(Enum):
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"
    IGNORED = "ignored"
    REMOVED = "removed"
    CONCAT_WIP = "concat_wip"  # concat in progress
    CONCAT_DONE = "concat_done"
    CONCAT_FAILED = "concat_failed"


class DiscoverStatus(Enum):
    TO_BE_TREATED = "to_be_treated"
    DOWNLOADED = "downloaded"
    BLACKLISTED = "blacklisted"
    WHITELSITED = "whitelisted"
    DOWNLOAD_MORE = "download_more"


@dataclass
class Creator:
    creator_id: str
    service: str
    domain: str
    status: Optional[str]


@dataclass
class Video:
    # important fields
    post_id: str
    creator_id: str
    service: str
    domain: str
    relative_path: str
    url: str
    part: int = 0

    # metadata
    published: Optional[str] = None
    title: Optional[str] = None
    substring: Optional[str] = None
    downloaded_at: Optional[str] = None
    file_size: Optional[float] = None

    # status in cdl
    status: Optional[VideoStatus] = None
    fail_count: int = 0
