# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [Unreleased]

## [1.4.0]

### Added

- `_resolve_args` now supports string
- error handling added to `_resolve_args`
- `from_raw` added to `DictEntry` and `ListEntry`

### Changed

- kwargs moved to `_resolve_entry`
- kwargs uses `DictEntry`

## [1.3.6]

### Fixed

- minor bug related to `FnWithKwargs` fixed

## [1.3.5]

### Fixed

- `test` and `docs` moved to dependency-groups

## [1.3.4]

### Changed

- readme updated

## [1.3.3]

### Fixed

- building project fixed

## [1.3.2]

### Fixed

- caching fixed in `ModuleEntry`

## [1.3.1]

### Changed

- referencing variables fixed

## [1.3.0]

### Added

- `Storage` class added

### Changed

- using `ModuleLoader` for loading modules

## [1.2.1]

### Fixed

- absolute or relative path fixed
- caching fixed in general

## [1.2.0]

### Added

- `Plugin` added
- new test cases added for plugin support

## [1.1.1]

### Added

- `hf` plugin added as an optional dependency

## [1.1.0]

### Changed

- using new parser for str variables
- `.` changed to `.{}`

## [1.0.1]

### Fixed

- adding `is_path_like` to check path-like strings

## [1.0.0]

### Added

- parser now supports import modules

### Changed

- module rearranged
- `args.` changed to `.`

## [0.2.1]

### Added

- caching added to `ModuleEntry`

## [0.2.0]

### Added

- entry classes added
- tests added with github action

## [0.1.0]

### Added

- list and dict supported now

### Changed

- `ConfigParser` cleaned up

## [0.0.2]

### Changed

- `README.md` updated

## [0.0.1]

### Added

- project init
