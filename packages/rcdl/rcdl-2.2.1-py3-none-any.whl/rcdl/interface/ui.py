# interface/ui.py

import logging
from rich.console import Console, Group
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich import box
from rich.live import Live
from rich.text import Text
from rcdl.core.models import VideoStatus, Creator


class UI:
    console = Console()
    logger = logging.getLogger()

    _video_progress_text: Text | None = None
    _concat_progress_text: Text | None = None
    _live: Live | None = None

    @staticmethod
    def _log_to_file(log_level, msg: str):
        log_level(msg)

    @classmethod
    def success(cls, msg: str):
        """Print success msg"""
        cls.console.print(f"[green]{msg}[/]")

    @classmethod
    def info(cls, msg: str):
        """Print & log info msg"""
        cls.console.print(msg)
        cls._log_to_file(cls.logger.info, msg)

    @classmethod
    def debug(cls, msg: str):
        """Print & log debug msg"""
        cls.console.print(f"[dim]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def warning(cls, msg: str):
        """Print & log warning msg"""
        cls.console.print(f"[yellow]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def error(cls, msg: str):
        """Print & log error msg"""
        cls.console.print(f"[red]{msg}[/]")
        cls._log_to_file(cls.logger.debug, msg)

    @classmethod
    def db_videos_status_table(cls, info: dict):
        """
        Print to cli a table with info of numbers of videos per status.
        Take in arg a dict: {
            "not_downloaded": int,
            "downloaded": int, "failed: int", "skipped: int", "ignored: int"}
        """

        table = Table(title="DB Videos status")

        table.add_column("Video status")
        table.add_column("Number of videos")

        for status in VideoStatus:
            name = status.value.replace("_", " ").capitalize()
            table.add_row(name, str(info[status.value]))

        cls.console.print(table)

    @classmethod
    def table_creators(cls, creators: list[Creator]):
        """Print to cli a table with all creators in creators.txt. Format is Creator ID | Service"""
        table = Table(title="Creators", box=box.MINIMAL, show_lines=True)
        table.add_column("Creators ID")
        table.add_column("Service")
        for creator in creators:
            table.add_row(creator.creator_id, creator.service)
        cls.console.print(table)

    @classmethod
    def progress_posts_fetcher(cls, max_pages: int):
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=cls.console,
            transient=False,  # remove progress bar after finish
        )
        return progress

    @classmethod
    def video_progress(cls, total: int):
        """Create video download progress output"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=cls.console,
            transient=False,  # remove the bar after completion
        )

        cls._video_progress_text = Text("Waiting...", style="Cyan")
        group = Group(progress, cls._video_progress_text)
        cls._live = Live(group, console=cls.console)
        cls._live.__enter__()

        task = progress.add_task("Downloading videos", total=total)
        return progress, task

    @classmethod
    def set_current_video_progress(cls, creator_info: str, filename: str):
        """Update video download output
        args:
            creator_info: str =  'creator_id@(service)'
            filename: str = video.relative_path
        """
        if cls._video_progress_text is None:
            return
        cls._video_progress_text.plain = ""
        cls._video_progress_text.append(f"{creator_info} -> ", style="Cyan")
        cls._video_progress_text.append(filename, style="green")

    @classmethod
    def close_video_progress(cls):
        """Close video progress"""
        if cls._live:
            cls._live.__exit__(None, None, None)
            cls._live = None

    @classmethod
    def concat_progress(cls, total: int):
        """Create concat progress bat"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=cls.console,
            transient=False,  # remove the bar after completion
        )

        cls._concat_progress_text = Text("Waiting...", style="Cyan")
        group = Group(progress, cls._concat_progress_text)
        cls._live = Live(group, console=cls.console)
        cls._live.__enter__()

        task = progress.add_task("Concatenating videos", total=total)
        return progress, task

    @classmethod
    def set_current_concat_progress(cls, msg: str, filename: str):
        """Update video download output
        args:
            creator_info: str =  'creator_id@(service)'
            filename: str = video.relative_path
        """
        if cls._concat_progress_text is None:
            return
        cls._concat_progress_text.plain = ""
        cls._concat_progress_text.append(f"{msg} -> ", style="Cyan")
        cls._concat_progress_text.append(filename, style="green")

    @classmethod
    def close_concat_progress(cls):
        """Close video progress"""
        if cls._live:
            cls._live.__exit__(None, None, None)
            cls._live = None

    @classmethod
    def progress_total_concat(cls):
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=cls.console,
            transient=False,  # remove progress bar after finish
        )
        return progress
