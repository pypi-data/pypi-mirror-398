# RCDL

Riton Coomer Download Manager  
`rcdl` is a tool to automatically download the videos of your favorites creators from [coomer.st](https://coomer.st) and [kemono.cr](https://kemono.cr)


## Install
### Dependencies
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [aria2](https://github.com/aria2/aria2)
- [ffmpeg](https://www.ffmpeg.org/download.html) (Only for `fuse` command)  
Recommended install:
```bash
pipx install yt-dlp
sudo apt install aria2 ffmpeg
```
### Install RCDL
It is recommended to use pipx
```bash
pipx install rcdl
```
or else:  
```bash
pip install rcdl
```

## How to use

Run the CLI with:

```bash
rcdl --help
```

By default all files will live in `~/Videos/rcdl/`. Cache, configuration and log file will be in a hidden `rcdl/.cache/` folder.

```bash
rcdl refresh    # look creators.json and find all possible videos
rcdl dlsf       # download all found videos
rcdl discover   # WIP
rcdl fuse       # WIP
rcdl log        # debug only; show the log file
```

Add, rm, list a creator:
```bash
rcdl add [URL]
rcdl add [service]/[creator_id]
```

## Dev
### Install
```bash
git clone https://github.com/ritonun/cdl.git rcdl
cd rcdl
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Deploy
```bash
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine
pip install flit packaging requests   # necessary to run auto release scripts

# Use convenience scripts in rcdl/scripts
# Create api_key.txt with the pypi api key in the root folder
python3 rcdl/scripts/upload_pypi.py
python3 rcdl/scripts/migrate_old_format_to_db.py
```
