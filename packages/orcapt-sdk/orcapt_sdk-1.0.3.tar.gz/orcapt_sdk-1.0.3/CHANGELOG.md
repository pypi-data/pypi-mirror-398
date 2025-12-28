# Changelog

All notable changes to Orca SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-15

### Added

- **Lambda Adapter**: Complete AWS Lambda deployment support

  - Automatic HTTP, SQS, and Cron event handling
  - Event loop management for Python 3.11+
  - Automatic SQS queuing when `SQS_QUEUE_URL` exists
  - Production-ready templates and examples

- **Storage SDK**: Integrated file storage management

  - `OrcaStorage` client for unified storage operations
  - Support for bucket management, file operations, and permissions
  - Complete API wrapper for Orca Storage

- **Design Patterns**: Professional pattern implementations

  - `OrcaBuilder` and `SessionBuilder` for fluent interfaces
  - Context managers for resource management
  - Middleware system with chain of responsibility
  - Type guards for runtime type safety

- **Documentation**: Comprehensive guides
  - Lambda deployment guide
  - Storage SDK developer guide
  - Quick reference and developer guide
  - 8+ complete examples with templates

### Changed

- **Architecture**: Complete refactoring to SOLID principles
  - 14 distinct layers for better separation of concerns
  - Dependency injection throughout
  - Interface-based design for testability
- **Session Management**: Improved composition

  - Split into focused operation modules
  - Better separation of concerns
  - Cleaner API surface

- **Error Handling**: Enhanced error system
  - Custom exception hierarchy
  - Better error context and tracing
  - Automatic error logging

### Improved

- **Type Safety**: 100% type hint coverage
- **Code Quality**: Comprehensive decorators and utilities
- **Logging**: Professional logging configuration with rotation
- **Testing**: Expanded test coverage and examples

### Documentation

- New README with better structure
- Complete API documentation
- Deployment guides for Lambda
- Security and contributing guidelines
- Example templates for quick start

## [1.0.0] - 2024-XX-XX

### Added

- Initial release
- Basic streaming functionality
- Real-time communication with Centrifugo
- Button rendering
- Loading indicators
- Error handling
- Usage tracking
- Tracing support

### Features

- Development mode with in-memory streaming
- Production mode with Centrifugo
- Thread-safe buffering
- API client for backend communication

## [Unreleased]

### Planned

- Enhanced caching mechanisms
- Additional storage backends
- Improved middleware system
- More deployment adapters (Cloud Run, ECS, etc.)

---

## Version History

### Version 2.x.x

- Focus on production readiness and deployment
- Professional architecture and patterns
- Lean dependency surface for core streaming operations

### Version 1.x.x

- Initial SDK with core streaming features
- Basic error handling and tracking

---

## Upgrade Guide

### Migrating from 1.x to 2.x

#### Breaking Changes

1. **Import Changes**:

```python
# Old (1.x)
from orca.unified_handler import OrcaHandler

# New (2.x)
from orca import OrcaHandler
```

2. **Session API**:

```python
# Old (1.x)
session.start_loading("thinking")
session.end_loading("thinking")

# New (2.x)
session.loading.start("thinking")
session.loading.end("thinking")
```

3. **Button API**:

```python
# Old (1.x)
session.button_link("Click", "https://example.com")

# New (2.x)
session.button.link("Click", "https://example.com")
```

#### New Features Available

- Lambda deployment via `LambdaAdapter`
- Storage management via `OrcaStorage`
- Design patterns via `OrcaBuilder`, middleware, etc.

#### Deprecated (Still Works)

The old flat session API still works for backward compatibility but will be removed in 3.0:

```python
# These still work but are deprecated:
session.start_loading()  # Use: session.loading.start()
session.button_link()    # Use: session.button.link()
```

---

## Support

For questions or issues:

- Email: support@orca.ai
- Discord: https://discord.gg/orca
- GitHub: https://github.com/your-org/orca-sdk/issues
