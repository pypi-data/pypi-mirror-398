# Changelog

## [0.2.0] - 2024-12-24

### Changed
- **Code Generation Mode**: Rainfall now generates and executes real Python code instead of just returning values
- Default model changed to `gemini-3-flash-preview`
- Added `requests` and `Pillow` as dependencies for generated code

### Added
- Generated code is cached per function (same function = same implementation)
- Syntax validation with automatic retry on errors
- Pre-imported modules: os, sys, json, re, math, datetime, pathlib, requests, PIL

## [0.1.0] - 2024-12-24

### Added
- Initial release
- CLI tool `rainfall` to run Python scripts with AI-powered stub functions
- Gemini API integration
- Automatic detection of stub functions
- Verbose and dry-run modes
