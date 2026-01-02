# scripts/migrage_creators_json_txt.py

import os
import json

from rcdl.core.models import Creator
from rcdl.core.config import Config
from rcdl.core.parser import get_domain, append_creator

JSON_PATH = Config.CACHE_DIR / "creators.json"

# check file exist
if not os.path.exists(JSON_PATH):
    print("creators.json deoes not exist. Check")

# load file
with open(JSON_PATH, "r") as f:
    json_creators = json.load(f)

# convert to Creator
creators = []
for json_creator in json_creators:
    creators.append(
        Creator(
            creator_id=json_creator["creator_id"],
            service=json_creator["service"],
            domain=get_domain(json_creator["service"]),
            status=None,
        )
    )

# save creator
for c in creators:
    append_creator(c)
    print(f"Saved new creator: {c.service}/{c.creator_id}")

print(f"You can now delete {JSON_PATH}")
