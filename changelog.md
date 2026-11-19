# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Test that EOF after one approved Bash overwrite preserves all remaining existing files.
- Document the Bash scaffolder test command and requirements in the contribution guide.
- Initial project structure
- Basic documentation

### Changed

### Deprecated

### Removed

### Fixed
- Keep documentation and .gitignore versionable and preserve the literal Python class pattern in Bash scaffolding.
- Preserve existing directories when rerunning the Bash scaffolder and skip file overwrites on EOF.

### Security
- Reject symlink destinations and parents in the Bash scaffolder before writing.
