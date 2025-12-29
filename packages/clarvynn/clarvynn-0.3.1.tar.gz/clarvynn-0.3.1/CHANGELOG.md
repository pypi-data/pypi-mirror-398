# Changelog

All notable changes to Clarvynn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2025-12-26

### Fixed
- **Log Filtering**: Fixed critical bug where log filtering was not working due to OTel SDK 1.39+ `ReadWriteLogRecord` nesting `trace_id` in `.log_record.trace_id` instead of direct attribute access.
- **Trace ID Extraction**: Added `_extract_trace_id()` helper to handle both OTel 1.20-1.38 (direct `trace_id`) and 1.39+ (nested `.log_record.trace_id`) formats.
- **Duplicate Log Exports**: Fixed duplicate log exports by deduplicating `LoggingHandler` instances on root logger.
- **Log Processor Attribute Mismatch**: Fixed bug where log processor deduplication could read from one attribute (`_processors`) but write to a different attribute (`_log_record_processors`), causing stale state and silent log filtering failures.
- **logging.basicConfig Blocking**: Fixed issue where `logging.basicConfig` was blocked when Clarvynn's bridge handler and OTel's `LoggingHandler` were already attached to root logger.
- **Default Log Level**: Changed Clarvynn's internal logging default from `info` to `warning` to reduce verbosity.

### Added
- **Test Coverage**: Added `TestTraceIdExtraction` class with 3 tests using REAL OTel objects (not mocks) to prevent SDK API regressions.
- **CI Coverage**: Extended `test_otel_compatibility.py` to test BOTH span and log processors across OTel SDK versions.
- **ReadWriteLogRecord Check**: Added explicit check for `ReadWriteLogRecord.log_record.trace_id` nesting in CI compatibility script.
- **Regression Tests**: Added `test_logging_configuration.py` with tests for `basicConfig` patching and handler deduplication.

### Changed
- Test suite expanded from 336 to 341 tests.

### Compatibility  
- **OpenTelemetry SDK**: 1.25.0 - 1.39.0 (tested)
- **Python**: 3.9, 3.10, 3.11, 3.12

## [0.3.0] - 2025-12-18

### Added
- Span buffering: child spans buffered until local root ends for complete trace context
- FIFO eviction: oldest trace exported when buffer full (10K traces max)
- TTL cleanup: orphaned traces exported after 60s (prevents OOM)
- Per-trace limits: max 50 spans, overflow exported immediately
- Trace criticality: if ANY child matches CPL, entire trace exported
- 32 new tests for span buffering, eviction, TTL, shutdown, attribute extraction

### Fixed
- Race condition in deferred evictions (copy/clear now atomic under lock)
- `duration_ms` attribute now correctly set for CPL slow request conditions
- `force_flush()` now exports all buffered spans
- `shutdown()` exports buffered spans, records decisions, flushes logs, clears state
- Overflow handling marks trace as critical for consistency

### Changed
- Test suite expanded from 304 to 336 tests

### Compatibility  
- **OpenTelemetry SDK**: 1.25.0 - 1.39.0 (tested)
- **Python**: 3.9, 3.10, 3.11, 3.12

## [0.2.2] - 2025-12-18

### Fixed
- **Logging**: Fixed critical bug where `[clarvynn]` prefix appeared on ALL application logs, not just Clarvynn's internal logs
  - Now uses dedicated `clarvynn` logger instead of modifying root logger
  - Set `propagate=False` to prevent logs bubbling to root logger
  - Removed auto-configure on module import to prevent interference with app logging
  - Added `SafeStreamHandler` to suppress I/O errors during process shutdown/test teardown

### Compatibility  
- **OpenTelemetry SDK**: 1.25.0 - 1.39.0 (tested)
- **Python**: 3.9, 3.10, 3.11, 3.12

## [0.2.1] - 2025-12-15

### Changed
- **CPL Engine**: Unified condition parsing on pyparsing, removed legacy regex-based parser
- **Smart Defaults**: Improved `clarvynn init` template with error/slow request conditions
- **Documentation**: Added `enabled` field documentation to CPL_REFERENCE.md

### Fixed
- **CI**: Lowered throughput test thresholds to 20K decisions/sec for CI runners (pyparsing is slower than regex but more robust)
- **Shutdown**: Fixed `ValueError: I/O operation on closed file` during logging shutdown with try/except guards

### Removed
- **Dead Code**: Removed unused `rate` field validation and `export` section from CLI (not part of CPL spec)

### Compatibility  
- **OpenTelemetry SDK**: 1.25.0 - 1.39.0 (tested)
- **Python**: 3.9, 3.10, 3.11, 3.12

## [0.2.0] - 2025-12-10


### Added
- Span/log interception pipeline that reuses OTel’s auto-configured processors via processor→exporter adapters, preserving user exporter config.
- Regression/compat tests:
  - Log interception + span/log correlation/Flight Recorder buffering.
  - Env matrix for console/otlp/none/unknown exporter settings.
  - CI job `otel-compat` to run OTel SDK version sweep script.

### Changed
- Shared log buffer now sharded (lock striping); benchmarks updated to avoid internal access.
- Configurator/env tests use dummy OTLP exporters to avoid network/import issues during CI.

### Fixed
- Log processor now tolerates ReadWriteLogRecord without `trace_id` (no AttributeError during startup).
- Removed internal terminology from adapters docstrings.

### Compatibility
- **OpenTelemetry SDK**: 1.25.0 - 1.39.0 (tested)
- **Python**: 3.9, 3.10, 3.11, 3.12

## [0.1.0] - 2024-12-04

Initial public release of Clarvynn - the control plane for OpenTelemetry that enforces Purposeful Observability through Deferred Head Sampling.

### Added
- Comprehensive test suite (296 tests, 100% pass rate)
  - Unit tests for CPL engine, policy cache, production adapter
  - Integration tests for span processor, log processor, TraceState exporter
  - Thread-safety and performance benchmarks
  - Test documentation in `tests/README.md`
- OpenTelemetry SDK compatibility testing script (`scripts/test_otel_compatibility.py`)


### Changed
- Simplified CPL schema: removed unused `rate` field from conditions
  - Matched conditions are now always sampled at 100% (the core value proposition)
  - `base_rate` still controls probabilistic sampling for unmatched traffic
- Cleaned up ProductionCPLAdapter to focus on file-only mode (current implementation)
  - Removed unused gRPC parameters and background sync code
  - Future dynamic updates will be implemented via file watching
- **Breaking**: Updated log processor to support OTel SDK 1.39+ API changes
  - `LogData` class removed in 1.39, now uses `ReadWriteLogRecord` directly
  - Backward compatible with 1.20-1.38 via version detection

### Fixed
- Improved hash distribution for timestamp-based log sampling using golden ratio constant
- Fixed documentation inconsistencies (package name, API examples, policy format)
- Fixed CLI import paths (`adapters.base` → `core.cpl_engine.python.base`)
- Removed obsolete pytest filterwarnings for `LogDeprecatedInitWarning` (removed in 1.39)

### Compatibility
- **OpenTelemetry SDK**: Tested and verified with versions 1.25.0 - 1.39.0
  - Narrowed from 1.20.0 to reduce maintenance burden
  - Users on older SDK versions should upgrade (1.25.0 released March 2024)
- **Python**: Supports 3.9, 3.10, 3.11, 3.12 (Python 3.8 EOL October 2024)

### Planned
- File watching for automatic policy reload (hot-reload)
- Java adapter support
- Node.js adapter support
- Go adapter support
- Rust-based CPL engine with WebAssembly
- Web UI for policy management

---

## [0.1.0] - Unreleased

### Initial Release

**Status:** Alpha - Ready for testing and early adoption

This is the first public release of Clarvynn! While we consider this production-quality code, the API may evolve based on user feedback before v1.0.0.

### Added

#### Core Features
- **Tail-based sampling** for OpenTelemetry Python applications
  - Sampling decisions made AFTER span completion (sees errors, latency, all attributes)
  - Dramatically more accurate than head-based sampling
  
- **CPL (Conditions-based Policy Language)**
  - Human-readable YAML-based policy definition
  - 10 condition patterns supported:
    - Error detection (`status_code >= 500`)
    - Latency thresholds (`duration_ms > 1000`)
    - HTTP method filtering (`method == "POST"`)
    - Path-based rules (`path contains "/api"`)
    - Logical operators (`AND`, `OR`, `NOT`)
    - Comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`, `contains`, `not contains`)
    - Parentheses for precedence (`(A OR B) AND C`)
  - Full expression parser using `pyparsing`
  
- **W3C TraceContext Level 2 support**
  - Consistent distributed sampling using `tracestate`
  - Critical traces marked with `ot=th:0` for 100% downstream capture
  - Complete end-to-end traces for errors/slow requests across microservices
  
- **Log-trace correlation**
  - Logs sampled consistently with their associated traces
  - No orphaned logs or traces
  - Trace decision cache for cross-signal consistency

#### OpenTelemetry Integration
- **Zero-code-change integration** via `opentelemetry-instrument`
- Drop-in replacement for standard OpenTelemetry configuration
- Works with existing auto-instrumentation libraries:
  - Flask (`opentelemetry-instrumentation-flask`)
  - Django (`opentelemetry-instrumentation-django`)
  - FastAPI (`opentelemetry-instrumentation-fastapi`)

#### CLI Tools
- `clarvynn init` - Generate starter policy configuration
- `clarvynn validate` - Validate policy syntax and structure
- Environment variable configuration:
  - `CLARVYNN_ENABLED` - Enable/disable Clarvynn
  - `CLARVYNN_POLICY_PATH` - Path to policy YAML file
  - `CLARVYNN_LOG_LEVEL` - Set log verbosity (debug, info, warning, error, silent)

#### Developer Experience
- Comprehensive examples for Flask, Django, FastAPI
- Policy templates for common use cases
- Detailed documentation:
  - Getting Started Guide
  - Configuration Reference
  - Framework Integration Guide
  - Architecture Deep Dive
  - CPL Language Reference
  - W3C TraceContext Level 2 Explanation

### Performance
- Sub-millisecond policy evaluation (< 50µs typical)
- Minimal memory overhead (< 10MB)
- Zero impact when disabled
- Efficient policy caching

### Compatibility
- **OpenTelemetry SDK**: 1.20.0 - 1.38.0 (tested)
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

### Documentation
- Complete API documentation
- 5-minute quick start guide
- Real-world examples
- Troubleshooting guide
- Adapter development guide (for future language support)

### Known Limitations
- **Python only** - Java/Node.js/Go support planned for v2.0.0
- **CLI only** - No web UI yet (planned for future release)
- **Limited operators** - More CPL operators will be added based on user feedback
- **OTLP export only** - Other exporters (Jaeger, Zipkin) planned for future releases

### Breaking Changes
- None (initial release)

### Migration Guide
- None (initial release)

---

## Version History

- **v0.1.0** (Jan 2025) - Initial alpha release
- **v1.0.0** (Planned Q2 2025) - Production-ready, stable API
- **v2.0.0** (Planned Q3 2025) - Multi-language support with Rust/Wasm

---

## How to Upgrade

### From source installation to v0.1.0
```bash
pip install clarvynn==0.1.0
```

### Future upgrades
```bash
# Check current version
pip show clarvynn

# Upgrade to latest
pip install --upgrade clarvynn

# Upgrade to specific version
pip install clarvynn==0.2.0
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

---

## Support

- **GitHub Issues**: https://github.com/clarvynn/clarvynn/issues
- **Discussions**: https://github.com/clarvynn/clarvynn/discussions
- **Documentation**: https://github.com/clarvynn/clarvynn/tree/main/docs

---

[Unreleased]: https://github.com/clarvynn/clarvynn/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/clarvynn/clarvynn/releases/tag/v0.1.0

