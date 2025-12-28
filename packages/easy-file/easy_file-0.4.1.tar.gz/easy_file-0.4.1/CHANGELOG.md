# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2025-12-25

### Fixed
- Release workflow configuration

## [0.4.0] - 2025-12-25

### Added
- `copy_async()` - async file copying
- `append_text_async()` - async text appending
- `read_bytes_async()` / `write_bytes_async()` - async binary operations
- `move()` / `move_async()` - move/rename files with auto parent directory creation
- `indent` parameter to `dump_json()` and `dump_json_async()` for JSON formatting control
- Typed deserialization with `dataclasses` and `TypedDict` for JSON/YAML
- Custom exceptions: `FileOperationError`, `JSONDecodeError`, `YAMLDecodeError`
- Atomic writes for `dump_json()` and `dump_yaml()`
- `atomic_write()` context manager
- Async methods: `read_text_async()`, `write_text_async()`, `load_json_async()`, `dump_json_async()`, `load_yaml_async()`, `dump_yaml_async()`
- `append_text()` utility method
- `touch_parents()` - create file and parent directories
- `size` property
- Automatic directory creation on write

## [Unreleased]

### Added
