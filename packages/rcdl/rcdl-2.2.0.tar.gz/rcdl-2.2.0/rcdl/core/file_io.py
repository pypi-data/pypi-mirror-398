# core/file_io.py

import json


def write_json(path, data, mode="w"):
    with open(path, mode) as f:
        json.dump(data, f, indent=4)


def load_json(path) -> dict:
    with open(path, "r") as f:
        data = json.load(f)
    return data


def load_txt(path) -> list[str]:
    with open(path, "r") as f:
        lines = f.readlines()
    for i in range(len(lines)):
        lines[i] = lines[i].strip()
    return lines


def write_txt(path, lines: list[str] | str, mode: str = "a"):
    if isinstance(lines, str):
        lines = [lines]

    with open(path, mode) as f:
        for line in lines:
            if not line.endswith("\n"):
                f.write(line + "\n")
            else:
                f.write(line)
