# Changelog

All notable changes to the kiarina-utils-common package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.20.1] - 2025-12-25

### Changed
- No changes

## [1.20.0] - 2025-12-19

### Changed
- No changes

## [1.19.0] - 2025-12-19

### Changed
- No changes

## [1.18.2] - 2025-12-17

### Changed
- No changes

## [1.18.1] - 2025-12-16

### Changed
- No changes

## [1.18.0] - 2025-12-16

### Changed
- No changes

## [1.17.0] - 2025-12-15

### Changed
- No changes

## [1.16.0] - 2025-12-15

### Changed
- No changes

## [1.15.1] - 2025-12-14

### Changed
- No changes

## [1.15.0] - 2025-12-13

### Changed
- No changes

## [1.14.0] - 2025-12-13

### Changed
- No changes

## [1.13.0] - 2025-12-09

### Changed
- No changes

## [1.12.0] - 2025-12-05

### Changed
- No changes

## [1.11.2] - 2025-12-02

### Added
- `ConfigStr` type alias for configuration string format documentation

## [1.11.1] - 2025-12-01

### Changed
- No changes

## [1.11.0] - 2025-12-01

### Changed
- No changes

## [1.10.0] - 2025-12-01

### Added
- `import_object` function for dynamic object importing from import paths (useful for plugin systems)

## [1.9.0] - 2025-11-26

### Changed
- No changes

## [1.8.0] - 2025-10-24

### Changed
- No changes

## [1.7.0] - 2025-10-21

### Changed
- No changes

## [1.6.3] - 2025-10-13

### Changed
- No changes

## [1.6.2] - 2025-10-10

### Changed
- No changes

## [1.6.1] - 2025-10-10

### Changed
- No changes

## [1.6.0] - 2025-10-10

### Changed
- No changes

## [1.5.0] - 2025-10-10

### Changed
- No changes

## [1.4.0] - 2025-10-09

### Changed
- No changes

## [1.3.0] - 2025-10-05

### Changed
- No changes

## [1.2.0] - 2025-09-25

### Changed
- No changes

## [1.1.1] - 2025-09-11

### Changed
- No changes

## [1.1.0] - 2025-09-11

### Changed
- No changes

## [1.0.1] - 2025-09-11

### Changed
- No changes - version bump for consistency with other packages

## [1.0.0] - 2025-09-09

### Added
- Comprehensive README.md with usage examples and API documentation
- Enhanced pyproject.toml with proper metadata, classifiers, and project URLs
- CHANGELOG.md for tracking version changes

### Changed
- Improved package documentation and metadata

## [0.1.0] - 2025-01-09

### Added
- Initial release of kiarina-utils-common
- `parse_config_string` function for parsing configuration strings
- Support for nested keys using dot notation
- Support for array indices in configuration strings
- Automatic type conversion (bool, int, float, str)
- Flag support (keys without values)
- Customizable separators for different parsing needs
- Comprehensive test suite with pytest
- Type hints and py.typed marker for full typing support

### Features
- Parse configuration strings like `"cache.enabled:true,db.port:5432"`
- Support for nested structures: `{"cache": {"enabled": True}, "db": {"port": 5432}}`
- Array index support: `"items.0:first,items.1:second"` → `{"items": ["first", "second"]}`
- Flag functionality: `"debug,verbose"` → `{"debug": None, "verbose": None}`
- Custom separators: configurable item, key-value, and nested separators
- Automatic type detection and conversion for common data types
