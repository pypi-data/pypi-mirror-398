# scripts/upload_pypi.py

import subprocess
import sys
import os
import requests
from packaging.version import parse as parse_version
import tomllib

# config
PYPROJECT_FILE = "pyproject.toml"
PYPI_PACKAGE_NAME = "rcdl"  # PyPI package name

# read local version
with open(PYPROJECT_FILE, "rb") as f:
    data = tomllib.load(f)

local_version = data["project"]["version"]
print(f"Local version: {local_version}")

# check remote latest version
response = requests.get(f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json")
if response.status_code == 200:
    latest_version = response.json()["info"]["version"]
    print(f"Latest PyPI version: {latest_version}")
else:
    latest_version = None
    print("ERROR: Package not found on PyPI")

# chec version number
if latest_version and parse_version(local_version) <= parse_version(latest_version):
    print("Error: Local version is not higher than PyPI version.")
    sys.exit(1)

# build with flit
print("Building package...")
subprocess.run([sys.executable, "-m", "flit", "build"], check=True)

# upload to pypi
print("Uploading to PyPI...")
if not os.path.exists("api_key.txt"):
    print(
        "ERROR - you have to create an api_key.txt file in your root directory containing only your pypi api key"
    )
    quit()
with open("api_key.txt", "r") as f:
    api_key = f.read().strip()
if api_key == "":
    print("ERROR - api_key.txt is empty")

subprocess.run(
    [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "-u",
        "__token__",
        "-p",
        api_key,
        "dist/*",
    ],
    check=True,
)

print("PYPI Upload complete!")

# find wheel file in dist/
dist_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
if not dist_files:
    raise FileNotFoundError("No .whl file found in dist/")

whl_file_path = os.path.join("dist", dist_files[0])
if local_version not in whl_file_path:
    raise FileNotFoundError("Version of .whl does not match upload.")

# create github release
tag = f"v{local_version}"
print(f"Creating github release {tag}")


subprocess.run(
    [
        "gh",
        "release",
        "create",
        tag,
        "--title",
        f"Release {tag}",
        "--notes",
        "",
        whl_file_path,
    ],
    check=True,
)

print("GitHub release created!")
print("--END--")
