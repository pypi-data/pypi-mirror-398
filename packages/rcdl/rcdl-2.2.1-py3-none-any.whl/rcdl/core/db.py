# core/db.py

"""Handle SQL DB and DB Parsing"""

import sqlite3
import logging
from typing import Iterable


import rcdl.core.db_queries as queries
from .config import Config
from .models import Video, VideoStatus


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")  # check input into db
        self.conn.execute("PRAGMA journal_mode = WAL")  #
        self.conn.execute("PRAGMA synchronous = NORMAL")  # faster write speed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def init_table(self):
        # init table for videos to DL
        self.conn.execute(queries.CREATE_VIDEOS_TABLE)
        self.conn.execute(queries.CREATE_IDX_VIDEOS_STATUS)
        self.conn.execute(queries.CREATE_IDX_VIDEOS_CREATOR)
        self.conn.execute(queries.CREATE_IDX_VIDEOS_FAIL_COUNT)

        # init table for version schem, easy migration if necessary
        self.conn.execute(queries.CREATE_SCHEMA_VERSION_TABLE)

        # Initialize version if empty
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM schema_version")
        row = cur.fetchone()
        if row["cnt"] == 0:
            cur.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))

        self.conn.commit()

    def get_schema_version(self) -> int:
        # get current db version -> for future update to db
        cur = self.conn.cursor()
        cur.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        return row["version"] if row else 0

    def set_schema_version(self, version: int):
        # set current db version
        self.conn.execute("UPDATE schema_version SET version = ?", (version,))
        self.conn.commit()

    def _row_to_video(self, row: sqlite3.Row) -> Video:
        # helper function to retunr Video model from a sql result
        return Video(
            post_id=row["post_id"],
            creator_id=row["creator_id"],
            service=row["service"],
            domain=row["domain"],
            relative_path=row["relative_path"],
            url=row["url"],
            part=row["part"],
            status=VideoStatus(row["status"]),
            fail_count=row["fail_count"],
            published=row["published"],
            title=row["title"],
            substring=row["substring"],
            downloaded_at=row["downloaded_at"],
            file_size=row["file_size"],
        )

    def query_videos(
        self,
        *,
        status: VideoStatus | Iterable[VideoStatus] | None = None,
        creator_id: str | None = None,
        post_id: str | None = None,
        max_fail_count: int | None = None,
        min_part_number: int | None = None,
        pending: bool = False,
    ) -> list[Video]:
        """
        Query the DB.
        Parametes are 'AND' so if video status and creator_id are sepcified,
        it will look for a match between the two

        pending:
        No parameters are taken into account if pending True.
        Look for videos with: NOT DOWNLOADED status OR (FAILED & fail_count < Config.max_fail_count)
        """
        sql = "SELECT * FROM videos"
        conditions = []
        params = []

        if pending:
            sql += " WHERE status = ? OR (status = ? AND fail_count < ?)"
            params.extend(
                [
                    VideoStatus.NOT_DOWNLOADED.value,
                    VideoStatus.FAILED.value,
                    max_fail_count or Config.MAX_FAIL_COUNT,
                ]
            )
        else:
            if status is not None:
                if isinstance(status, VideoStatus):
                    conditions.append("status = ?")
                    params.append(status.value)
                else:
                    statuses = list(status)
                    placeholders = ",".join("?" for _ in statuses)
                    conditions.append(f"status IN ({placeholders})")
                    params.extend(s.value for s in statuses)

            if creator_id is not None:
                conditions.append("creator_id = ?")
                params.append(creator_id)

            if post_id is not None:
                conditions.append("post_id = ?")
                params.append(post_id)

            if max_fail_count is not None:
                conditions.append("fail_count < ?")
                params.append(max_fail_count)

            if min_part_number is not None:
                conditions.append("part > ?")
                params.append(min_part_number)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        logging.debug(f"SQL CMD: {sql} with params: {params}")
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        if Config.DEBUG:
            logging.debug(f"DB query returned {len(rows)} result")

        return [self._row_to_video(r) for r in rows]

    def get_db_videos_info(self):
        """Return number of videos per status
        return info: dict {
            "not_downloaded": int,
            "failed": int,
            etc...
        }
        """
        info = {}
        for status in VideoStatus:
            vids = self.query_videos(status=status)
            info[status.value] = len(vids)
        return info

    def set_status(
        self, video: Video, status: VideoStatus, *, fail_count: int | None = None
    ):
        """Set video status to specified status"""
        video.status = status
        if fail_count is not None:
            video.fail_count = fail_count
        self._upsert_video(video)

    def insert_videos(self, videos: list[Video]):
        """
        Insert a video if not already present. Else ignore.
        Does not modify any values
        """
        if not videos:
            return

        rows = []
        for video in videos:
            rows.append(
                (
                    video.post_id,
                    video.creator_id,
                    video.service,
                    video.domain,
                    video.relative_path,
                    video.url,
                    video.part,
                    VideoStatus.NOT_DOWNLOADED.value,
                    0,
                    video.published,
                    video.title,
                    video.substring,
                    None,
                    None,
                )
            )

        self.conn.executemany(queries.INSERT_IGNORE_VIDEO_UPSERT, rows)
        self.conn.commit()

    def _upsert_video(self, video: Video):
        """Upsert a video.
        If video already in DB, update specifics fields:
             status, fail_count, relative path, file_size, downloaded_at
        """
        if video.status is None:
            video.status = VideoStatus.NOT_DOWNLOADED

        self.conn.execute(
            queries.INSERT_VIDEO_UPSERT,
            (
                video.post_id,
                video.creator_id,
                video.service,
                video.domain,
                video.relative_path,
                video.url,
                video.part,
                video.status.value,
                video.fail_count,
                video.published,
                video.title,
                video.substring,
                video.downloaded_at,
                video.file_size,
            ),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
