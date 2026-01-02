# core/fuse.py

import os

from rcdl.interface.ui import UI
from rcdl.core.db import DB
from rcdl.core.models import VideoStatus
from rcdl.core.config import Config
from rcdl.core.downloader_subprocess import ffmpeg_concat


def fuse_videos():
    """Fuse videos"""

    allowed_status = [
        VideoStatus.DOWNLOADED,
        VideoStatus.CONCAT_WIP,
        VideoStatus.CONCAT_FAILED,
        VideoStatus.CONCAT_DONE,  # dev only remove
    ]

    # load db videos
    with DB() as db:
        videos = db.query_videos(status=allowed_status, min_part_number=1)

    # get unique posts id
    posts_ids = set()
    for video in videos:
        posts_ids.add(video.post_id)

    with UI.progress_total_concat() as progress:
        task = progress.add_task("Total concat", total=len(posts_ids))

        for post_id in posts_ids:
            UI.info(f"Looking at post_id: {post_id}")

            # get all videos with same post_id
            with DB() as db:
                videos = db.query_videos(post_id=post_id)
            if not videos:
                UI.error("Query SQL Failed.")
                progress.update(task, advance=1)
                continue

            # check each videos of the same post is fully downloaded
            ok = True
            for video in videos:
                if video.status not in allowed_status:
                    ok = False
                    break
            if not ok:
                progress.update(task, advance=1)
                continue

            # sort by part number
            videos.sort(key=lambda v: int(v.part))

            ok = True
            for video in videos:
                # make sure video exist
                path = os.path.join(
                    Config.creator_folder(video.creator_id), video.relative_path
                )
                if not os.path.exists(path):
                    UI.error(f"Video @ {path} does not exists")
                    ok = False

                # if status is concat WIP, these should not be possible
                if video.status == VideoStatus.CONCAT_WIP:
                    UI.warning(
                        f"Video '{video.relative_path}' has status 'CONCAT_WIP'. This is a bug and should not be possible."
                    )

            # update videos status in db to CONCAT_WIP
            # in case of problems in the scripts, we will know
            with DB() as db:
                for video in videos:
                    db.set_status(video, VideoStatus.CONCAT_WIP)

            result = 1
            try:
                result = ffmpeg_concat(videos)
            except Exception as e:
                UI.error(f"Failed concat due to: {e}")

            # concat failed
            if not result == 0:
                with DB() as db:
                    for video in videos:
                        db.set_status(video, VideoStatus.CONCAT_FAILED)

            # concat succeeded
            with DB() as db:
                for video in videos:
                    db.set_status(video, VideoStatus.CONCAT_DONE)

            progress.update(
                task,
                advance=1,
                description=f"Concated videos for post id {post_id}",
            )
