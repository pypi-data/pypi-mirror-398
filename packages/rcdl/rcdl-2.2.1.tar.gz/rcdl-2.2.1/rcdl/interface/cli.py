# interface/cli.py

import logging

import click

from rcdl.core import downloader as dl
from rcdl.core.config import Config
from rcdl.core.parser import (
    get_creators,
    get_creator_from_line,
    parse_creator_input,
    append_creator,
)
from rcdl.core.db import DB
from .ui import UI
from rcdl.core.fuse import fuse_videos


from rcdl import __version__


@click.command(help="Refresh video to be downloaded")
def refresh():
    """Refresh database with creators videos

    - get all creators from creators.txt
    - for each creators find all videos and put them in the database
    No download is done in this command
    """

    UI.info("Welcome to RCDL refresh")
    dl.refresh_creators_videos()

    with DB() as db:
        info = db.get_db_videos_info()

    UI.db_videos_status_table(info)


@click.command(help="Download all videos from all creator")
def dlsf():
    """Download video based on DB information

    - read databse
    - for each video NOT_DOWNLOADED or FAILED & fail_count < settings, dl video
    """
    UI.info("Welcome to RCDL dlsf")
    dl.download_videos_to_be_dl()


@click.command("fuse", help="Fuse part video into one")
def fuse():
    """Fuse videos"""
    UI.info("fuse")
    fuse_videos()


@click.command(help="Discover videos/creators with tags")
@click.option("--tag", required=True, type=str, help="Tag to search for")
@click.option(
    "--max-page", default=10, type=int, help="Maximum number of pages to fetch"
)
def discover(tag, max_page):
    """Discover new creators/videos
    currently WIP. Do not use in prod"""
    msg = f"[cdl] discover with tag={tag} max_page={max_page}"
    click.echo(msg)
    logging.info(msg)
    dl.discover(tag, max_page)


@click.command("add", help="Add a creator")
@click.argument("creator_input")
def add_creator(creator_input):
    """Add a creator (URL or str) to creators.txt"""
    service, creator_id = parse_creator_input(creator_input)
    line = f"{service}/{creator_id}"
    creator = get_creator_from_line(line)
    if creator is not None:
        append_creator(creator)
        UI.info(f"Added {line} to creators.txt")
    else:
        UI.warning("Could not extract creator from input. Please check input is valid")


@click.command("remove", help="Remove a creator")
@click.argument("creator_input")
def remove_creator(creator_input):
    """Remove a creator (excat line) from creators.txt"""
    _service, creator_id = parse_creator_input(str(creator_input))

    creators = get_creators()
    all_creators = []
    matched_creator = None
    for creator in creators:
        if creator.creator_id == creator_id:
            matched_creator = creator
            continue
        all_creators.append(creator)

    if matched_creator is None:
        UI.error(f"Could not find creator from {creator_input}")
        return
    else:
        open(Config.CREATORS_FILE, "w").close()
        for c in all_creators:
            append_creator(c)
        UI.info(
            f"Removed creator {matched_creator.creator_id}@({matched_creator.service})"
        )


@click.command("list", help="List all creators")
def list_creators():
    creators = get_creators()
    UI.table_creators(creators)


# --- CLI GROUP ---
@click.group()
@click.option("--debug", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.version_option(version=__version__, prog_name=Config.APP_NAME)
def cli(debug, dry_run):
    Config.set_debug(debug)
    Config.set_dry_run(dry_run)


cli.add_command(dlsf)
cli.add_command(discover)
cli.add_command(refresh)
cli.add_command(add_creator)
cli.add_command(remove_creator)
cli.add_command(list_creators)
cli.add_command(fuse)
