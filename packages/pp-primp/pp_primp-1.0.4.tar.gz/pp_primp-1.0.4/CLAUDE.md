# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRIMP (Python Requests IMPersonate) is a high-performance Python HTTP client library that can impersonate web browsers by mimicking their headers and TLS/JA3/JA4/HTTP2 fingerprints. It's built as a Rust extension using PyO3 and the rquest library.

## Architecture

### Core Components

**Rust Layer (src/)**
- `lib.rs` - Main PyO3 module exposing `RClient` class with HTTP methods (get, post, etc.). Uses a global Tokio single-threaded runtime (`RUNTIME`) to execute async operations while releasing Python's GIL
- `impersonate.rs` - Browser/OS impersonation logic with string-to-enum conversion traits. Supports "random" selection from predefined lists
- `response.rs` - Response handling with lazy content loading, encoding detection, and HTML conversion (markdown, plain, rich text). Includes streaming support via `ResponseStream`
- `traits.rs` - Extension traits for converting between IndexMap and HeaderMap types
- `utils.rs` - CA certificate loading from webpki-root-certs and environment variables

**Python Layer (primp/)**
- `__init__.py` - Wraps Rust `RClient` with `Client` and `AsyncClient` classes. `AsyncClient` uses `asyncio.run_in_executor` to run synchronous methods asynchronously
- `primp.pyi` - Type stubs for IDE support

### Key Design Patterns

1. **Lazy Loading**: Response properties (content, headers, cookies, encoding) are computed on first access and cached
2. **Thread Safety**: Client uses `Arc<Mutex<rquest::Client>>` for safe concurrent access
3. **GIL Release**: All I/O operations use `py.allow_threads()` to release Python's GIL during blocking operations
4. **Single Runtime**: Global Tokio runtime shared across all client instances to avoid overhead

## Development Commands

### Building

Build Rust extension in debug mode:
```bash
maturin develop
```

Build release version:
```bash
maturin build --release
```

Build with specific Python version:
```bash
maturin develop --python 3.12
```

### Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_client.py
```

Run with verbose output:
```bash
pytest -v
```

### Linting & Type Checking

Format Python code:
```bash
ruff format primp/ tests/
```

Lint Python code:
```bash
ruff check primp/ tests/
```

Type check:
```bash
mypy primp/
```

Format Rust code:
```bash
cargo fmt
```

Lint Rust code:
```bash
cargo clippy
```

### Benchmarking

Install benchmark dependencies:
```bash
pip install -r benchmark/requirements.txt
```

Start benchmark server:
```bash
uvicorn benchmark.server:app --host 0.0.0.0 --port 8000
```

Run benchmark:
```bash
python benchmark/benchmark.py
```

Generate benchmark image:
```bash
python benchmark/generate_image.py
```

## Important Implementation Details

### Environment Variables

- `PRIMP_PROXY` - Default proxy URL if not specified in client
- `PRIMP_CA_BUNDLE` - Path to custom CA certificate bundle

### Client Initialization Flow

1. Impersonation settings are applied first (determines headers/TLS fingerprint)
2. Custom headers override default impersonation headers
3. Proxy is loaded from parameter or `PRIMP_PROXY` environment variable
4. CA certificates loaded from `ca_cert_file`, `PRIMP_CA_BUNDLE`, or webpki-root-certs (in that order)

### Request Body Handling

Only POST, PUT, PATCH methods support request bodies. Body types are mutually exclusive:
- `content` - Raw bytes
- `data` - Form-encoded data
- `json` - JSON-encoded data
- `files` - Multipart file upload

### Impersonate "random" Feature

When `impersonate="random"`, a random browser is selected from `IMPERSONATE_LIST` in `src/impersonate.rs`. Note: `okhttp_3.9` and `okhttp_3.11` are commented out in the random list due to FAILURE_ON_CLIENT_HELLO issues.

## CI/CD

The project uses GitHub Actions (`.github/workflows/CI.yml`) for:
- Building wheels for Linux (x86_64, aarch64, armv7), musllinux, Windows (x64), macOS (x86_64, aarch64)
- Running pytest across Python 3.8-3.13 on all platforms
- Publishing to PyPI on tagged releases
- Running benchmarks and updating benchmark images on releases

Cross-compilation for ARM uses platform-specific toolchains and QEMU for testing.

## Testing Patterns

Tests use a `@retry` decorator for flaky network operations. They validate:
- Client initialization parameters
- Request methods (GET, POST, etc.) with various body types
- Cookie handling (get/set)
- Header management
- Authentication (basic and bearer)
- Proxy support
- Response properties (status_code, headers, cookies, content, json, text)
- Streaming responses
- Async client functionality

Test files mirror the structure: `test_client.py`, `test_asyncclient.py`, `test_response.py`, `test_defs.py`.
