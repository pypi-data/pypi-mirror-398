# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-05

### Added
- Initial release of Salesforce Toolkit
- JWT Bearer Flow authentication
- OAuth 2.0 Password Flow authentication
- Generic Salesforce client for CRUD operations
- Support for any Salesforce object (standard and custom)
- Field mapping engine with transformations
- Sync pipeline framework for ETL operations
- Comprehensive logging system with rotation
- Command-line interface (CLI)
- Configuration via YAML files
- Utility functions for common Salesforce operations
- Batch operations support
- Automatic query pagination
- Complete documentation and examples

### Features
- Create, Read, Update, Delete operations on any Salesforce object
- Bulk create via Composite API
- Upsert support with external ID fields
- SOQL query execution with automatic pagination
- Field mapping with nested field access (dot notation)
- Built-in transformations (lowercase, uppercase, date formatting, etc.)
- Custom transformation functions
- Multiple sync modes (INSERT, UPDATE, UPSERT, DELETE)
- Progress tracking with callbacks
- Colored console logging
- File logging with rotation
- Environment-based configuration
- CLI commands for common operations

### Documentation
- Comprehensive README with examples
- API reference documentation
- Usage examples for all major features
- Configuration templates
- YAML configuration examples

## [Unreleased]

### Planned
- Bulk API 2.0 support for large-scale operations
- Metadata API integration
- Streaming API support (PushTopic, Generic Streaming)
- Built-in retry mechanism with exponential backoff
- Dry-run mode for sync pipelines
- Performance metrics and monitoring
- Integration with popular ORMs

---

For more details, see the [README.md](README.md).
