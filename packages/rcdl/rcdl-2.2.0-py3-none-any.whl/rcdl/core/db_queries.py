# core/db_queries.py

"""
Hold all the SQL commands strings
"""

CREATE_VIDEOS_TABLE = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT,
    creator_id TEXT,
    service TEXT,
    domain TEXT,
    relative_path TEXT,
    url TEXT,
    part TEXT,
    status TEXT DEFAULT 'not_downloaded',
    fail_count INTEGER DEFAULT 0,
    published TEXT,
    title TEXT,
    substring TEXT,
    downloaded_at TEXT,
    file_size REAL,
    UNIQUE (service, url)
)
"""

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
)
"""

INSERT_VIDEO_UPSERT = """
INSERT INTO videos (
    post_id, creator_id, service, domain, relative_path, url, part,
    status, fail_count, published, title, substring,
    downloaded_at, file_size
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(service, url) DO UPDATE SET
    status = excluded.status,
    fail_count = excluded.fail_count,
    relative_path = excluded.relative_path,
    downloaded_at = excluded.downloaded_at,
    file_size = excluded.file_size
"""

INSERT_IGNORE_VIDEO_UPSERT = """
INSERT OR IGNORE INTO videos (
    post_id, creator_id, service, domain, relative_path, url, part, 
    status, fail_count, published, title, substring, 
    downloaded_at, file_size
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

CREATE_IDX_VIDEOS_STATUS = (
    "CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)"
)
CREATE_IDX_VIDEOS_CREATOR = (
    "CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_id)"
)
CREATE_IDX_VIDEOS_FAIL_COUNT = (
    "CREATE INDEX IF NOT EXISTS idx_videos_fail_count ON videos(fail_count)"
)
