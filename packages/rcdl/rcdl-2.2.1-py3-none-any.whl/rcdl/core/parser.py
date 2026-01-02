# core/parser.py

import logging
from pathvalidate import sanitize_filename

from .models import Video, VideoStatus, Creator
from .file_io import load_json, load_txt, write_txt
from .config import Config
from rcdl.interface.ui import UI


COOMER_PAYSITES = ["onlyfans", "fansly", "candfans"]
KEMONO_PAYSITES = [
    "patreon",
    "fanbox",
    "fantia",
    "boosty",
    "gumroad",
    "subscribestar",
    "dlsite",
]


def get_domain(arg: str | dict | Video) -> str:
    """From a service get the domain (coomer or kemono)
    Input is either: service(str), post(dict), video(models.Video)
    """

    def _service(service: str) -> str:
        if service in COOMER_PAYSITES:
            return "coomer"
        if service in KEMONO_PAYSITES:
            return "kemono"
        logging.error(f"Service {service} not associated to any domain")
        return ""

    if isinstance(arg, dict):
        return _service(arg["service"])
    elif isinstance(arg, Video):
        return _service(arg.service)

    return _service(arg)


def get_title(post: dict) -> str:
    """Extract title from a post(dict)"""
    title = post["title"]
    if title == "":
        if "content" in post:
            title = post["content"]
        elif "substring" in post:
            title = post["substring"]
    return sanitize_filename(title)


def get_date(post: dict) -> str:
    """Extract date from a post(dict)"""
    if "published" in post:
        date = post["published"][0:10]
    elif "added" in post:
        date = post["added"][0:10]
    else:
        logging.error(f"Could not extract date from {post['id']}")
        date = "NA"
    return date


def get_part(post: dict, url: str) -> int:
    """
    For posts containing multiple video url. Each url is considered a part,
    so all videos from the same posts will simply have a different part number
    """
    urls = extract_video_urls(post)
    part = 0
    if len(urls) == 1:
        return 0

    for u in urls:
        if u == url:
            return part
        part += 1

    logging.error(
        f"Could not extract part number for post id {post['id']} with url {url}"
    )
    return -1


def get_filename(post: dict, url: str) -> str:
    title = get_title(post)
    date = get_date(post)
    part = get_part(post, url)
    file_title = f"{date}_{title}".replace("'", " ").replace('"', "")
    filename = f"{file_title}_p{part}.mp4"
    return filename


def convert_post_to_video(post: dict, url: str, discover=False) -> Video:
    part = get_part(post, url)
    title = get_title(post)
    date = get_date(post)
    filename = get_filename(post, url)

    if discover:
        filename = f"{post['user']}_{post['id']}.mp4"

    return Video(
        post_id=post["id"],
        creator_id=post["user"],
        service=post["service"],
        relative_path=filename,
        url=url,
        domain=get_domain(post),
        part=part,
        published=date,
        title=title,
        status=VideoStatus.NOT_DOWNLOADED,
        fail_count=0,
    )


def convert_posts_to_videos(posts: list[dict], discover: bool = False) -> list[Video]:
    videos = []
    for post in posts:
        urls = extract_video_urls(post)
        if not discover:
            for url in urls:
                videos.append(convert_post_to_video(post, url))
        else:
            if len(urls) == 0:
                continue
            videos.append(convert_post_to_video(post, urls[0], discover=discover))
    return videos


def extract_video_urls(post: dict) -> list:
    video_extensions = (".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v")
    urls = set()

    # Check main file
    if post["file"]:
        if post["file"]["path"]:
            path = post["file"]["path"]
            if path.endswith(video_extensions):
                urls.add(f"{path}")

    if post["attachments"]:
        attachments = post["attachments"]
        for attachment in attachments:
            if attachment["path"]:
                if attachment["path"].endswith(video_extensions):
                    urls.add(f"{attachment['path']}")

    return list(urls)


def filter_posts_with_videos_from_list(data: list[dict]) -> list[dict]:
    """Return posts with video url from a json with a list of posts"""

    posts_with_videos = []
    for post in data:
        if len(extract_video_urls(post)) > 0:
            posts_with_videos.append(post)
    return posts_with_videos


def filter_posts_with_videos_from_json(path: str) -> list:
    """Return posts with video url from a json with a list of posts"""
    posts = load_json(path)

    posts_with_videos = []
    for post in posts:
        if len(extract_video_urls(post)) > 0:
            posts_with_videos.append(post)
    return posts_with_videos


def valid_service(service: str) -> bool:
    if service in COOMER_PAYSITES:
        return True
    if service in KEMONO_PAYSITES:
        return True
    return False


def get_creator_from_line(line: str) -> Creator | None:
    """
    Convert a line into a Creator model
    arg: line -> 'service/creator'
    This is the format of creators.txt
    """
    parts = line.split("/")
    if valid_service(parts[0].strip()):
        return Creator(
            creator_id=parts[1].strip(),
            service=parts[0].strip(),
            domain=get_domain(parts[0].strip()),
            status=None,
        )
    elif valid_service(parts[1].strip()):
        return Creator(
            creator_id=parts[0].strip(),
            service=parts[1].strip(),
            domain=get_domain(parts[1].strip()),
            status=None,
        )
    else:
        UI.error(
            f"Creator file not valid: {line} can not be interpreted. Format is: 'service/creator_id'"
        )
    return None


def get_creators() -> list[Creator]:
    """
    Load creators.txt and return a list of models.Creator
    """
    lines = load_txt(Config.CREATORS_FILE)
    creators = []
    for line in lines:
        creator = get_creator_from_line(line)
        if creator is None:
            continue
        creators.append(creator)
    if len(creators) < 1:
        UI.error(f"Could not find any creators. Check {Config.CREATORS_FILE}")
    return creators


def get_creators_from_posts(posts: list[dict]) -> list[Creator]:
    creators = list()
    seen = set()

    for post in posts:
        key = (post["user"], post["service"], "coomer")
        if key in seen:
            continue

        seen.add(key)
        creators.append(
            Creator(
                creator_id=post["user"],
                service=post["service"],
                domain="coomer",
                status="to_be_treated",
            )
        )
    return creators


def parse_creator_input(value: str) -> tuple[str | None, str]:
    value = value.strip()

    # url
    if "://" in value:
        parts = value.replace("https://", "").strip().split("/")
        logging.info(f"From {value} extracte service {parts[1]} and creator {parts[3]}")
        return parts[1], parts[3]  # service, creator_id

    # creators.txt format
    if "/" in value:
        c = get_creator_from_line(value)
        if c is not None:
            logging.info(
                f"From {value} extracte service {c.service} and creator {c.creator_id}"
            )
            return c.service, c.creator_id

    logging.info(f"From {value} extracte service None and creator {value}")
    return None, value


def append_creator(creator: Creator):
    line = f"{creator.service}/{creator.creator_id}"
    lines = load_txt(Config.CREATORS_FILE)

    if line in lines:
        return
    lines.append(line)
    write_txt(Config.CREATORS_FILE, line, mode="a")
