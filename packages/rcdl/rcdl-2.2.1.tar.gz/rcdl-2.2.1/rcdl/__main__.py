# __main__.py

import logging

from rcdl.core.config import Config, setup_logging

# setup file structure
Config.ensure_dirs()
Config.ensure_files()

# setup logging
setup_logging(Config.LOG_FILE, level=0)

logging.info("--- INIT ---")
logging.info("Logger initialized")

# init database
from rcdl.core.db import DB  # noqa: E402

db = DB()
db.init_table()
logging.info(f"DB version: {db.get_schema_version()}")
db.close()

from rcdl.interface.cli import cli  # noqa: E402, F401
