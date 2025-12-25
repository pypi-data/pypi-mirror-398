# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.3.7 - 2025-12-23

### Fixed

- Enhanced query sanitization by prioritizing backslash escaping to prevent double-escaping issues (#39).

## 0.3.6 - 2025-12-19

### Fixed

- Added hyphen/dash character to Elasticsearch query sanitization to prevent parsing errors.

## 0.3.5 - 2025-12-19

### Fixed

- Fixed Elasticsearch query parsing errors with special characters in user input (#37, #38)
- Added automatic sanitization for query_string.query fields to handle characters like `/`, `\`, `<`, `>`, `|`, `&`

## 0.3.4 - 2025-10-17

### Changed

- Increased httpx timeout for reading from 60 to 180 seconds in AsyncMRSClient.

## 0.3.3 - 2025-09-16

### Added

- Added traceback import neede for es_request() funcitonality (#35)

## 0.3.2 - 2025-09-04

### Added

- Added `requirements.txt` with runtime dependencies (`httpx`, `pydantic`, `xxhash`). (#33)

### Changed

- Updated `pymrs/__init__.py` exports and packaging metadata alignment. (#34)

## 0.3.1 - 2025-08-12

### Changed

- Enhanced `close()` method with `force_close` parameter for better session cleanup control.
- Improved resource management by selectively closing HTTP client based on authentication type.

## 0.3.0 - 2025-07-10

### Added

- Added `get_entities()` and `get_content()` methods for entity retrieval and content access to AsyncMRSClient class.

### Changed

- Enhanced `es_request()` method with better error handling, "EVERYTHING" permissions support, improved role-based filtering, and SSL/timeout handling.
- Improved ticket validation logic and general error handling throughout the codebase.

## 0.2.1 - 2025-06-18

### Changed

- Enhanced ticket-based authentication with better validation and session management.
- Improved async context manager support.
- Enhanced documentation and error handling.

## 0.2.0 - 2025-05-21

### Fixed 

- Fixed logging levels and security concerns (#24).
- Fixed hostname handling to support flexible rest server paths. Hostname parameter now expects the complete base URL including the rest server path.

### Added

- Added timeout customiztion through AsyncMRSClient (#25).
- Added method register_entities() in Query class with URI generation (#18 #19 #20 #26)
- Added method patch_entities() in Query class (#19)

## 0.1.3 - 2025-04-07

### Fixed

- Fixed bug with `eq` field in `_QueryPartOfJSON` class that caused type error.

## 0.1.2 - 2025-02-04

### Fixed

- Incorrect error handling in some cases (#23).

## 0.1.1 - 2024-12-12

### Changed

- Module directory from mrs to pymrs to post on PyPI.

### Fixed

- Short timeout in AsyncMRSClient (#21).

## 0.1.0 - 2024-11-11

- Initial release


