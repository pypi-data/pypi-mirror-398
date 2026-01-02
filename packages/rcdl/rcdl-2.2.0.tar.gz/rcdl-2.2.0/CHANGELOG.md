# Changelog

---
## [Unreleased]
### Added
- `fuse` command to automatically fuse videos that are in multiple parts
- Progress bar for concat of videos
---

## [2.1.1] - 2025-12-27
### Added
- `add`, `remove` and `list` commands added to manage creators
- Migrate scripts to migrate from pre-v2 folder structure to v2+. folder structure and db
- Print info of videos to download, already downloaded, etc... at the end of command `refresh`
- DB now has schema_version for future update/migration 
### Changed
- Logging in db only happens in debug mode
- Significantly improved cli print with `rich`
- `creators.json` replaced with `creators.txt`
### Fixed
- Log info of db status
- SQL Command bug preventing full execution of `dlsf`
- Fix % calculation in progress information
- PostsFetcher bug preventing `refresh` command to fully execute
### Removed
- Remove `fuse` commands. Will be reimplemented in the future

## [2.0.0] - 2025-12-25
### Added
- Renamed the project from `cdl` to `rcdl` !
- New command `refresh` to update video to be downloaded without starting the download
### Changed
- Default file creation changed (see config.py)
- Progress ETA improved
- Replaced .csv cache with `sqlite3` DB
- `refresh` functionnality removed from `dlsf`
### Fixed
- Fix multiple bugs

## [1.6.2] - 2025-12-21
### Fixed
- Fix empty '' ss duration
### Added
- Discovery command: search tags for posts with tag
- Tag and Max_page aoption arg

## [1.5.1] - 2025-10-21
### Added
- Fuse part videos with cdl fuse command. Warning: delete part videos that are succesfully fused.
- Preset selection in settings.json
- Data gatehring of fuse performance in .cache/fuse.csv
- Progress info for fuse command
### Changed
- Instead of deleting fused file, rename to .mv_oldfilename.mp4

## [1.4.1] - 2025-10-20
### Added
- Updated parser to extract .m4v video too
- Custom yt-dlp flags in "yt_dlp_args" in settings.json. aria2 call live here
### Fixed
- Fixed crash when looking for already downloaded posts and error index in .cache/ is missing
- Fixed issue when video is not written in cache, still check if video not in paths
- Fix bug when initialisation wrote default settings despite file already existing

## [1.3.1] - 2025-10-04
### Added
- Use aria2 as external downloader in yt-dlp
- Add --version flag
- Show log file in terminal with command cdl log
- Added DEBUG flag --debug, no functionnality yet
- Add support for kemono
### Changed
- Python version required now is >= 3.12 instead of >= 3.13
- Progress class to track progress, now also give an estimated time remaining
- Progress eta is now in HH:MM:SS format
- Change log file location
### Fixed
- Fix empty title bug
- Fix an issue when multiples URLS where in a post, it only checked if the first post had been downloaded and not all urls before skipping download

## [1.0.0] - 2025-10-03
### Added
- Initial release of the project
