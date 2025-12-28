# pykustomize

Python bindings for [Kustomize](https://kustomize.io/) - Kubernetes configuration customization.

**pykustomize** provides a complete Python wrapper for the Kustomize Go API, enabling you to build and customize Kubernetes configurations directly from Python. Following the architecture pattern of [helm-sdkpy](https://github.com/vantagecompute/helm-sdkpy), it creates a self-contained package with no system dependencies.

## ✨ Features

- 🚀 **Async-first API** - All operations use Python's `async/await` for non-blocking execution
- 📦 **Self-contained** - Bundles the Go library, no external kustomize binary needed
- 🔒 **Type-safe** - Full type hints for IDE support and static analysis
- 🎯 **Simple API** - Easy-to-use interface mirroring kustomize functionality
- ⚡ **Fast** - Native Go performance through FFI

## 📦 Installation

```bash
# Build the library first
just build-lib

# Install the package
pip install .

# Or install in development mode
pip install -e .
```

## 🚀 Quick Start

```python
import asyncio
from pykustomize import build, build_json, BuildOptions, LoadRestrictions

async def main():
    # Simple build - returns YAML
    result = await build("/path/to/kustomization")
    print(result.yaml)
    
    # Build with options
    options = BuildOptions(
        load_restrictions=LoadRestrictions.NONE,
        add_managedby_label=True,
    )
    result = await build("/path/to/overlay", options)
    
    # Build to JSON for programmatic access
    result_json = await build_json("/path/to/kustomization")
    for resource in result_json.resources:
        print(f"{resource['kind']}: {resource['metadata']['name']}")

asyncio.run(main())
```

## 📚 API Reference

### Kustomizer

The main class for performing kustomize operations.

```python
from pykustomize import Kustomizer, BuildOptions

kustomizer = Kustomizer()

# Build and get YAML
result = await kustomizer.build("/path/to/kustomization")
print(result.yaml)

# Build and get JSON
result = await kustomizer.build_json("/path/to/kustomization")
for resource in result.resources:
    print(resource)

# Get available plugins
plugins = await kustomizer.get_builtin_plugins()
print(plugins)
```

### BuildOptions

Configure how kustomize processes the kustomization.

```python
from pykustomize import BuildOptions, LoadRestrictions, ReorderOption

options = BuildOptions(
    # Control file loading (ROOT_ONLY is secure default)
    load_restrictions=LoadRestrictions.ROOT_ONLY,
    
    # Control output ordering
    reorder=ReorderOption.LEGACY,
    
    # Add managed-by label
    add_managedby_label=True,
    
    # Enable plugins
    enable_plugins=False,
    
    # Enable Helm chart inflation
    enable_helm=False,
    helm_command="/usr/local/bin/helm",
)
```

### LoadRestrictions

Controls what files can be loaded during kustomization.

| Value | Description |
|-------|-------------|
| `ROOT_ONLY` | Only allow loading files from within the kustomization root (secure default) |
| `NONE` | Allow loading files from anywhere (less secure, but more flexible) |

### ReorderOption

Controls the order of resources in the output.

| Value | Description |
|-------|-------------|
| `UNSPECIFIED` | Let kustomize select the appropriate default |
| `LEGACY` | Use a fixed order for backwards compatibility |
| `NONE` | Respect the depth-first resource input order |

### Convenience Functions

For simple use cases, use the module-level functions:

```python
from pykustomize import build, build_json

# Build to YAML
result = await build("/path/to/kustomization")

# Build to JSON
result = await build_json("/path/to/kustomization")
```

## 🛠️ Development

### Prerequisites

- Python 3.14+
- Go 1.22+
- Docker (for building the native library)
- [just](https://github.com/casey/just) (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/vantagecompute/pykustomize.git
cd pykustomize

# Install Python dependencies
uv sync

# Build the native library (using Docker)
just build-lib

# Or build locally if you have Go installed
just build-lib-local

# Run tests
just test
```

### Available Commands

```bash
just                # List all commands
just build-lib      # Build native library using Docker
just build-lib-local # Build native library locally
just test           # Run tests
just lint           # Check code style
just typecheck      # Run type checking
just fmt            # Format code
just clean          # Clean build artifacts
```

## 🏗️ Architecture

pykustomize follows a three-layer architecture:

```
┌─────────────────────────────────────┐
│     Python Application              │
│  (async/await, type hints)          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Python Layer (pykustomize)      │
│  - Kustomizer class                 │
│  - BuildOptions configuration       │
│  - Exception hierarchy              │
└──────────────┬──────────────────────┘
               │ asyncio.to_thread()
┌──────────────▼──────────────────────┐
│     FFI Layer (CFFI)                │
│  - C function bindings              │
│  - Type marshalling                 │
│  - Error handling                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Go Shim Layer (CGO)             │
│  - Wraps kustomize/api/krusty       │
│  - Thread-safe with mutex           │
│  - JSON serialization               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Kustomize Go Library            │
│  sigs.k8s.io/kustomize/api          │
└─────────────────────────────────────┘
```

## 📝 Examples

See the [examples/](examples/) directory for more usage examples.

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Vantage Compute

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing style (ruff formatting)
- Tests pass and coverage is maintained
- Type hints are included
- Documentation is updated
