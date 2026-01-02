# core/downloader.py

import logging
import os

import requests

import rcdl.core.parser as parser
from .api import URL
from .config import Config
from .models import Creator, Video, VideoStatus
from .db import DB
from .downloader_subprocess import ytdlp_subprocess
from .file_io import write_json, load_json
from rcdl.interface.ui import UI


class PostsFetcher:
    """
    Fetch posts from api. Save as JSON. Handle multiple pages requests
    """

    def __init__(
        self, url: str, json_path: str, max_page: int = Config.DEFAULT_MAX_PAGE
    ):
        self.url = url
        self.json_path = json_path

        self.page = 0
        self.max_page = max_page

        self.status = 200

    def _request_page(self, url: str) -> requests.Response:
        """Request a single page and return json dict"""
        logging.info(f"RequestEngine url {url}")
        headers = URL.get_headers()
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.warning(f"Failed request {url}: {requests.status_codes}")
        return response

    def request(self, params: dict = {}):
        with UI.progress_posts_fetcher(self.max_page) as progress:
            task = progress.add_task("Fetching posts", total=self.max_page)

            while self.status == 200 and self.page < self.max_page:
                o = self.page * Config.POST_PER_PAGE
                params["o"] = o
                url = URL.add_params(self.url, params)

                try:
                    # Dry run: not request acutally made
                    if Config.DRY_RUN:
                        logging.debug(
                            f"DRY-RUN posts fetcher {url} -> {self.json_path}"
                        )
                        self.page += 1
                        continue

                    response = self._request_page(url)
                    self.status = response.status_code

                    # if the programm crash while doing requests, previous requests are still saved and not overwritten.
                    if self.page > 0:
                        json_data = list(load_json(self.json_path))
                    else:
                        json_data = []

                    # for discover command, response json is in a different format and contains 'posts'
                    if self.status == 200:
                        if "posts" in response.json():
                            json_data.extend(response.json()["posts"])
                        else:
                            json_data.extend(response.json())

                        write_json(self.json_path, json_data, mode="w")

                    progress.update(
                        task,
                        advance=1,
                        description=f"Fetched {len(json_data)} posts (page {self.page + 1}/{self.max_page})",
                    )
                except Exception as e:
                    logging.error(f"Error in request {url} p{self.page}: {e}")
                finally:
                    self.page += 1


class VideoDownloader:
    """Handle downloading a list of Videos and update DB status"""

    def __init__(self):
        pass

    def _build_url(self, video: Video):
        return URL.get_url_from_file(video.domain, video.url)

    def _build_output_path(self, video: Video, discover: bool = False):
        if discover:
            return os.path.join(Config.DISCOVER_DIR, video.relative_path)

        return os.path.join(
            Config.creator_folder(video.creator_id), video.relative_path
        )

    def _update_db_status(self, result: int, video: Video):
        with DB() as d:
            if result == 0:
                d.set_status(video, VideoStatus.DOWNLOADED, fail_count=0)
            else:
                d.set_status(video, VideoStatus.FAILED, fail_count=video.fail_count + 1)

    def downloads(
        self, videos: list[Video], write_db: bool = True, discover: bool = False
    ):
        progress, task = UI.video_progress(total=len(videos))
        try:
            for video in videos:
                url = self._build_url(video)
                filepath = self._build_output_path(video, discover=discover)

                UI.set_current_video_progress(
                    f"{video.creator_id}@({video.service})", video.relative_path
                )

                if Config.DRY_RUN:
                    UI.debug(f"Dry run: dl {video.creator_id} @ {filepath}")
                    progress.advance(task)
                    continue

                if os.path.exists(filepath):
                    UI.warning(
                        f"Video {url} @ {filepath} already exists. Possible DB problem"
                    )
                    progress.advance(task)
                    continue

                result = ytdlp_subprocess(url, filepath)
                if write_db:
                    self._update_db_status(result, video)

                progress.advance(task)
        finally:
            UI.close_video_progress()


def fetch_posts_by_tag(tag: str, max_page: int = Config.DEFAULT_MAX_PAGE) -> dict:
    """Helper function to get all posts from a search results"""
    url = URL.get_posts_page_url_wo_param()
    path = Config.cache_file(tag)
    pf = PostsFetcher(url, str(path), max_page=max_page)
    pf.request(params={"tag": tag})

    return load_json(path)


def fetch_posts_by_creator(creator: Creator) -> dict:
    """Helper function to get all posts from a creator"""
    url = URL.get_creator_post_wo_param(creator)
    path = Config.cache_file(f"{creator.creator_id}_{creator.service}")
    pf = PostsFetcher(url, str(path))
    pf.request()

    return load_json(path)


def refresh_creators_videos():
    """
    Command refresh
    For each creator:
        - get all posts to a .json
        - from the .json filter to keep only the posts with videos in it
        - convert posts dict to Videos
        - update the DB
    """
    creators = parser.get_creators()
    for creator in creators:
        UI.info(f"Creator {creator.creator_id} from {creator.service}")

        fetch_posts_by_creator(creator)
        posts_with_videos = parser.filter_posts_with_videos_from_json(
            str(Config.cache_file(f"{creator.creator_id}_{creator.service}"))
        )
        all_videos = parser.convert_posts_to_videos(posts_with_videos)

        UI.info(
            f"Found {len(all_videos)} videos from {len(posts_with_videos)} posts with videos url"
        )

        # put all videos in db
        with DB() as db:
            db.insert_videos(all_videos)


def download_videos_to_be_dl():
    """
    Command dlsf
    Download videos in db with status TO_BE_DOWNLOADED OR (FAILED & fail_count < Config.)
    """
    with DB() as db:
        videos = db.query_videos(pending=True)

    vd = VideoDownloader()
    vd.downloads(videos, write_db=True, discover=False)


# --- --- --- --- --- DISCOVER --- --- --- --- ---
def discover(tag: str, max_page: int):
    discover_creators(tag, max_page)
    dl_video_from_discover_creators()


def discover_creators(tag: str, max_page: int):
    # download posts with searched tags
    posts = fetch_posts_by_tag(tag, max_page)
    logging.info(f"Find {len(posts)} post")

    path = str(Config.cache_file(tag))
    posts_with_videos = parser.filter_posts_with_videos_from_json(path)
    logging.info(f"Find {len(posts_with_videos)} posts with videos")

    creators = parser.get_creators_from_posts(posts_with_videos)

    # save to csv
    file = os.path.join(Config.DISCOVER_DIR, "discover.csv")
    with open(file, "w") as f:
        for c in creators:
            line = f"{c.creator_id};{c.service};{c.domain};{'to_be_treated'}\n"
            f.write(line)


def dl_video_from_discover_creators():
    # load csv
    file = os.path.join(Config.DISCOVER_DIR, "discover.csv")
    with open(file, "r") as f:
        lines = f.readlines()

    creators = []
    for line in lines:
        line = line.replace("\n", "").strip().split(";")
        creators.append(
            Creator(creator_id=line[0], service=line[1], domain=line[2], status=line[3])
        )

    # get posts
    for creator in creators:
        response = requests.get(
            URL.get_creator_post_wo_param(creator), headers=URL.get_headers()
        )
        if response.status_code != 200:
            print(f"ERROR - Request {URL.get_creator_post_wo_param(creator)}")
        response_posts = response.json()
        posts = parser.filter_posts_with_videos_from_list(response_posts)
        print(f"{len(posts)} found")
        if len(posts) > 5:
            posts = posts[0:5]
            print("Limited posts to 5")

        for post in posts:
            urls = parser.extract_video_urls(post)
            url = URL.get_url_from_file(creator.domain, urls[0])
            filename = f"{post['user']}_{post['id']}.mp4"
            filepath = os.path.join(Config.DISCOVER_DIR, filename)
            ytdlp_subprocess(url, filepath)
