# scripts/migrate_old_format_to_db.py

"""
Use this script to migrate from pre-2.0 to 2+.
Script migrate_old_format_to_db version: v1.0

old_format:
- no db
cdl/
    creator1/
        date_title1_p0.mp4
        date_title2_p0.mp4
        date_title2_p1.mp4
        ...
    ...

for each creator:
    - [x] get all posts
    - [x] match each videos to its posts
    - [x] update db
    - [ ] check db with local videos
"""

import logging
import os
from pathlib import Path
import shutil

from rcdl.core.config import Config
from rcdl.core.models import Creator, Video, VideoStatus
from rcdl.core.file_io import load_json
from rcdl.core.api import URL
from rcdl.core.db import DB
import rcdl.core.downloader as dl
import rcdl.core.parser as parser

Config.ensure_dirs()
Config.ensure_files()

with DB() as db:
    db.init_table()

CDL_PATH = Path.home() / "Videos" / "cdl"
CREATORS_JSON = CDL_PATH / ".cache" / "creators.json"
TEMP_JSON = str(CDL_PATH / "temp.json")
LOG_PATH = CDL_PATH / "migrate_log.log"
MV_TXT = CDL_PATH / "mv.txt"
DEST_BASE = Path("/home/elitedesk/Videos/rcdl")

logging.basicConfig(
    filename=LOG_PATH,
    filemode="a",
    encoding="utf-8",
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("{levelname}: {message}", style="{"))
logging.getLogger().addHandler(console)

open(MV_TXT, "w").close()


def add_to_mvtxt(filepath: str):
    with open(MV_TXT, "a") as f:
        f.write(filepath + "\n")


def update_db_info(video: Video):
    with DB() as db:
        db._upsert_video(video)


def move_files(mv_txt: Path, dest_base: Path):
    # Read all file paths
    i = 0
    with mv_txt.open("r", encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]

    for src_path_str in paths:
        src = Path(src_path_str)
        if not src.exists():
            print(f"Skipping missing file: {src}")
            i += 1
            continue

        # Compute destination folder
        relative_parts = src.parts[len(Path("/home/elitedesk/Videos/cdl").parts) :]
        dest_dir = dest_base.joinpath(*relative_parts[:-1])
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Destination path
        dest = dest_dir / src.name

        # Move the file
        shutil.move(str(src), str(dest))
        i += 1
        print(f"Moved ({i}/{len(paths)}): {src} -> {dest}")


if __name__ == "__main__":
    logging.info("--- MIGRATE pre-v2 to +2.0 Script START ---")

    # get all local creators
    creators_json = load_json(CREATORS_JSON)
    creators: list[Creator] = []
    for creator in creators_json:
        creators.append(
            Creator(
                creator_id=creator["creator_id"],
                service=creator["service"],
                domain=creator["domain"],
                status=None,
            )
        )

    for creator in creators:
        # get posts
        url = URL.get_creator_post_wo_param(creator)
        print(f"Request {url} up to {15} max page")
        pf = dl.PostsFetcher(url, TEMP_JSON, max_page=15)
        pf.request()

        posts = parser.filter_posts_with_videos_from_json(TEMP_JSON)
        print(f"Found {len(posts)} posts with videos for creator {creator.creator_id}")

        posts_videos = parser.convert_posts_to_videos(posts)
        print(f"Converted {len(posts)} to Video")
        for video in posts_videos:
            video.status = VideoStatus.DOWNLOADED

        # get local videos
        creator_path = os.path.join(CDL_PATH, creator.creator_id)
        print(f"Looking in {creator_path}")
        files = os.listdir(creator_path)

        local_videos: list[dict] = []
        for file in files:
            # ignore partial file
            if file.endswith(".part") or file.endswith(".aria2"):
                continue

            # remove ext
            name = file[:-4] if file.endswith(".mp4") else file

            # part number
            if "_p" not in name:
                print(f"Skipped file due to missing part number: {file}")

            try:
                base, part_str = name.rsplit("_p", 1)

                # extract date and title
                date, *title_parts = base.split("_")
                title = "_".join(title_parts)  # keeps underscores in title

                local_videos.append(
                    {
                        "date": date,  # e.g. "2025-12-25"
                        "title": title,
                        "part": part_str,  # e.g. "0"
                    }
                )
            except:  # noqa E277
                pass

        print(f"Found {len(local_videos)} local videos")

        # match local vid to videos list
        for lv in local_videos:
            for pv in posts_videos:
                if (
                    lv["date"] == pv.published
                    and lv["title"] == pv.title
                    and lv["part"] == str(pv.part)
                ):
                    print(f"Found a match for {pv.relative_path}")
                    update_db_info(pv)
                    add_to_mvtxt(os.path.join(creator_path, pv.relative_path))
                    break
            else:
                print(f"No match found {lv['date']}_{lv['title']}_{lv['part']}")

        move_files(MV_TXT, DEST_BASE)
        shutil.move(str(MV_TXT), str(MV_TXT) + f".{creator.creator_id}.txt")
        open(MV_TXT, "w").close()
