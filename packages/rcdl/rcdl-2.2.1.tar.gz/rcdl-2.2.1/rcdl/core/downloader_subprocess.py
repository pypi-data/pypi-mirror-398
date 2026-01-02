# core/downloader_subprocess.py

import subprocess
import logging
from pathlib import Path
import os

from rcdl.core.models import Video
from rcdl.core.config import Config
from rcdl.interface.ui import UI


def ytdlp_subprocess(
    url: str,
    filepath: Path | str,
):
    """Call yt-dlp in a subprocess"""
    cmd = [
        "yt-dlp",
        "-q",
        "--progress",
        url,
        "-o",
        filepath,
        "--external-downloader",
        "aria2c",
    ]

    logging.info(f"CMD: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"yt-dlp failed to dl vid: {result.stderr}")

    return result.returncode


def ffmpeg_concat_build_command(videos: list[Video]) -> dict:
    # parameters
    width: int = 1920
    height: int = 1080
    fps: int = 30
    preset: str = "veryfast"
    threads: int = 0  # 0 for max

    # output path
    v = videos[0]
    output_filename = f"tmp_{v.published}_{v.title}.mp4"
    output_path = os.path.join(Config.creator_folder(v.creator_id), output_filename)

    # build cmd
    cmd = ["ffmpeg", "-y", "-progress", "pipe:2", "-nostats"]

    # inputs
    for v in videos:
        input_path = os.path.join(Config.creator_folder(v.creator_id), v.relative_path)
        cmd.extend(["-i", input_path])

    # filter complex
    filter_lines = []
    for idx in range(len(videos)):
        filter_lines.append(
            f"[{idx}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={fps},setsar=1"
            f"[v{idx}]"
        )

    # concat inputs
    concat = []
    for idx in range(len(videos)):
        concat.append(f"[v{idx}][{idx}:a]")

    filter_lines.append(f"{''.join(concat)}concat=n={len(videos)}:v=1:a=1[outv][outa]")
    filter_complex = ";".join(filter_lines)

    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-threads",
            str(threads),
            "-c:a",
            "aac",
            "-f",
            "mp4",
            output_path,
        ]
    )

    return {"cmd": cmd, "output_path": output_path}


def get_duration(path: str) -> int:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return int(float(result.stdout.strip()) * 1000)


def get_total_duration(videos: list[Video]) -> int:
    duration = 0
    for v in videos:
        path = os.path.join(Config.creator_folder(v.creator_id), v.relative_path)
        duration += get_duration(path)
    return duration


def ffmpeg_concat(videos: list[Video]):
    command_builder = ffmpeg_concat_build_command(videos)
    cmd = command_builder["cmd"]
    output_path = command_builder["output_path"]

    logging.info(f"CMD: {' '.join(cmd)}")

    ffmpeg_log = Config.CACHE_DIR / "ffmpeg.log"
    with open(ffmpeg_log, "w", encoding="utf-8") as log_file:
        print(cmd, file=log_file)
        # run cmd
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        assert process.stderr is not None
        total_duration = get_total_duration(videos)
        progress, task = UI.concat_progress(total=total_duration)
        last_progress = 0
        UI.set_current_concat_progress(f"{videos[0].relative_path}", output_path)

        for line in process.stderr:
            line = line.strip()
            if not line:
                continue

            print(line, file=log_file)

            progres_key = "out_time_ms"
            if line.startswith(progres_key):
                current_progress_str = line.replace(f"{progres_key}=", "").strip()
                try:
                    current_progress_us = int(current_progress_str)
                    current_progress_ms = current_progress_us // 1000
                    delta = current_progress_ms - last_progress
                    progress.advance(task, advance=delta)
                    last_progress = current_progress_ms
                except Exception:
                    pass

        process.wait()
        UI.close_concat_progress()

    if process.returncode != 0:
        UI.error(f"Failed to concat videos. See ffmpeg log file {ffmpeg_log}")
        return process.returncode

    temp_output_path = output_path
    new_output_path = temp_output_path.replace("tmp_", "")
    os.replace(temp_output_path, new_output_path)
    UI.info(f"Rename {output_path} -> {output_path}")
    return 0
