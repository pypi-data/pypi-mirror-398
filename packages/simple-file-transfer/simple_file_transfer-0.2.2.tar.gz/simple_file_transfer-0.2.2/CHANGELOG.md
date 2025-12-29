# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-12-23

### Added
- Custom file ID support: `sft upload --id <custom_id> ./file.txt 1h`
- Server validation to reject duplicate custom file IDs

## [0.1.0] - 2024-12-22

### Added
- Initial release of Simple File Transfer
- Flask-based HTTP server for file storage
- CLI client with upload and download commands
- Automatic file expiry with configurable durations
- SHA256 checksum verification
- Docker support for easy deployment
- Time format parsing (m, h, d, w)
- Background cleanup of expired files
- Health check endpoint
- Comprehensive end-to-end tests
- Unit tests for server and CLI
- CI/CD workflows with GitHub Actions
- PyPI publishing automation
- Docker image publishing

### Features
- Upload files with expiry times (30m, 1h, 2d, 1w)
- Download files by ID
- Automatic cleanup of expired files
- File integrity verification with SHA256
- Simple deployment to Digital Ocean
- Docker containerization

[Unreleased]: https://github.com/yourusername/simple-file-transfer/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yourusername/simple-file-transfer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/simple-file-transfer/releases/tag/v0.1.0
