# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.4.9] - 2025-12-

### Added

- Lazy Markers for deferred resolution of injection references with @inject decorator
- Meta functions for dynamic injection resolution and internal behavior modification

### Changed

- Prefer use of LazyProvide over Provide for dependency injection for compatibility with meta functions

## [v0.4.8] - 2025-12-18

### Fixed

- Corrected import handling in provider injectable resolution

## [v0.4.7] - 2025-12-18

### Changed

- Refactored injectable definition and resolution logic
- Products are now injected like a normal dependency
- Improved code readability and maintainability
- Updated type hints for class decorators

### Removed

- Removed redundant wiring logic on injection resolution

## [v0.4.6] - 2025-11-27

### Added

- Stubs for dependency and library modules

### Fixed

- Removed unused casts for class decorators in type hints

## [v0.4.5] - 2025-10-27

## [v0.4.3] - 2025-08-11

### Added

- Allow @inject based dependency injection
- New circular dependency detection and handling

### Fixed

- Fixed issues with module decorator typing

### Changed

- Plugin config now retrieved from class type hint
- Improved dependency resolution and injection process

## [v0.4.0] - 2025-08-09

### Added

- New plugin system for better modularity
- Support for dynamic configuration loading
- Updated documentation for plugin development

### Changed

- Improved dependency resolution and injection process
