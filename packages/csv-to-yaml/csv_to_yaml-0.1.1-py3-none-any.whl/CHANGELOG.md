# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-12-22

### Changed

- CSV to YAML conversion now outputs a dictionary with row numbers as keys (1-indexed) instead of a plain list
- YAML to CSV conversion handles both the new row-number keyed format and legacy list format

## [0.1.0] - 2025-12-21

### Added

- Initial release
- Core CSV to YAML conversion with `csv_to_yaml()` function
- Core YAML to CSV conversion with `yaml_to_csv()` function
- File-to-file conversion helpers (`csv_file_to_yaml_file`, `yaml_file_to_csv_file`)
- Command-line interface with `csv-to-yaml` command
- Support for both string and file path inputs
- Auto-detection of output format based on file extension
- UTF-8 and BOM handling for CSV files
- Full Unicode support including Korean characters
- MIT License
