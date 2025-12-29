# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-12-26

### Changed
- Updated documentation and project metadata

### Fixed
- Minor bug fixes and improvements

## [0.1.0] - 2025-12-26

### Added
- Initial release of fastapi-autowire
- Spring-like dependency injection and autowiring for FastAPI applications
- Semantic component decorators: `@service`, `@repository`, `@component`, `@configuration`, and `@provider`
- Type-safe dependency injection using `Autowired[T]` generic type
- Automatic dependency resolution with topological sorting
- Circular dependency detection at startup
- Interface-based component registration with `as_type` parameter
- Lifecycle management with `post_construct()` and `shutdown()` hooks
- Application context (`AppContext`) for managing component instances
- Singleton scope for all registered components
- FastAPI lifespan integration for automatic startup and shutdown
- Constructor injection for component dependencies
- Route handler injection via FastAPI's `Depends()` mechanism
- Built-in logging system with dedicated `fastapi_autowire` logger
- Comprehensive test suite covering integration, lifecycle, and resolver functionality
- Full type annotations with `py.typed` marker for type checking support
- Support for Python 3.9, 3.10, 3.11, and 3.12
- Complete documentation in README.md with examples and diagrams

### Features
- **Semantic Decorators**: Use `@service`, `@repository`, `@component`, `@configuration`, and `@provider` for clear code organization
- **Automatic Dependency Resolution**: Dependencies are resolved automatically based on type hints using topological sorting
- **Type-Safe Autowiring**: Leverage `Autowired[T]` generic for compile-time type checking
- **Circular Dependency Detection**: Prevents circular dependencies and provides clear error messages
- **Interface-Based Registration**: Register concrete implementations against abstract base classes
- **Lifecycle Hooks**: Support for `post_construct()` initialization and `shutdown()`/`close()` cleanup methods
- **FastAPI Integration**: Seamless integration with FastAPI's dependency injection via custom lifespan manager
- **Application Context**: Centralized container for accessing registered components at runtime
- **Zero Runtime Overhead**: O(1) component lookup during request handling (singletons pre-instantiated at startup)
- **Debugging Support**: Built-in logging with configurable levels for troubleshooting dependency resolution

[Unreleased]: https://github.com/leoroop/fastapi-autowire/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/leoroop/fastapi-autowire/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/leoroop/fastapi-autowire/releases/tag/v0.1.0