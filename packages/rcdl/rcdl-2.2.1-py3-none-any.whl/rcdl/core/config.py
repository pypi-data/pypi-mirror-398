# core/config.py

from pathlib import Path
import logging
import os

from .file_io import write_txt


class Config:
    # paths
    APP_NAME = "rcdl"

    BASE_DIR = Path(os.environ.get("RCDL_BASE_DIR", Path.home() / "Videos/rcdl"))

    CACHE_DIR = BASE_DIR / ".cache"
    DB_PATH = CACHE_DIR / "cdl.db"
    LOG_FILE = CACHE_DIR / "cdl.log"
    FUSE_CSV_FILE = CACHE_DIR / "cdl_fuse.csv"
    CREATORS_FILE = CACHE_DIR / "creators.txt"
    DISCOVER_DIR = CACHE_DIR / "discover"

    # default creators
    DEFAULT_CREATORS = ["boixd/onlyfans"]

    DEBUG = False
    DRY_RUN = False

    # api settings
    POST_PER_PAGE = 50
    DEFAULT_MAX_PAGE = 10
    MAX_FAIL_COUNT = 7

    @classmethod
    def ensure_dirs(cls):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.DISCOVER_DIR.mkdir(exist_ok=True)

    @classmethod
    def ensure_files(cls):
        files = [
            cls.DB_PATH,
            cls.FUSE_CSV_FILE,
            cls.CREATORS_FILE,
        ]
        for file in files:
            if not file.exists():
                file.touch()
                logging.info("Created file %s", file)
                if file == cls.CREATORS_FILE:
                    write_txt(cls.CREATORS_FILE, cls.DEFAULT_CREATORS, mode="w")

    @classmethod
    def creator_folder(cls, creator_id: str) -> Path:
        folder = cls.BASE_DIR / creator_id
        folder.mkdir(exist_ok=True)
        return folder

    @classmethod
    def cache_file(cls, filename: str, ext: str = ".json") -> Path:
        file_name = filename + ext
        file = cls.CACHE_DIR / file_name
        return file

    @classmethod
    def set_debug(cls, debug: bool):
        cls.DEBUG = debug

    @classmethod
    def set_dry_run(cls, dry_run: bool):
        cls.DRY_RUN = dry_run


def setup_logging(log_file: Path, level: int = 0):
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()  # avoid double handlers if called multiple times

    # loggin format & file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setFormatter(
        logging.Formatter(
            "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    # log library warning/errors
    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)  # only show warnings/errors from libraries
    logger.addHandler(stream)
