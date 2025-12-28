# Copyright 2025 Vantage Compute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""FFI bindings for the pykustomize native library."""

from __future__ import annotations

import platform
import threading
from pathlib import Path
from typing import Any

from cffi import FFI  # type: ignore[import]

from .exceptions import KustomizeError, KustomizeLibraryNotFound

ffi: Any = FFI()
ffi.cdef(
    """
    // Error handling
    char* pykustomize_last_error(void);
    void pykustomize_free(void *ptr);

    // Version info
    char* pykustomize_version_string(void);
    int pykustomize_version_number(void);

    // Build operations
    int pykustomize_build(const char *path, const char *options_json, char **result);
    int pykustomize_build_to_json(const char *path, const char *options_json, char **result);

    // Plugin info
    int pykustomize_get_builtin_plugins(char **result);
    """
)


__all__ = [
    "KustomizeError",
    "KustomizeLibraryNotFound",
    "configure",
    "ffi",
    "get_library",
    "get_version",
    "string_from_c",
    "check_error",
    "_reset_for_tests",
]


_library_lock = threading.Lock()
_library = None
_library_path: str | None = None


def configure(path: str | None) -> None:
    """Force the bindings to load libpykustomize from ``path``.

    Passing ``None`` clears the override and re-enables auto-discovery.
    """
    global _library_path, _library
    with _library_lock:
        _library_path = path
        _library = None


def _find_library() -> str | None:
    """Find the pykustomize shared library."""

    # Check for configured path first
    if _library_path is not None:
        return _library_path

    # Determine platform-specific library name and search paths
    system = platform.system()
    machine = platform.machine()

    # Normalize architecture names to match Go's convention
    if machine == "x86_64":
        machine = "amd64"
    elif machine == "aarch64":
        machine = "arm64"

    if system == "Linux":
        lib_name = "libpykustomize.so"
        platform_dir = f"linux-{machine}"
    elif system == "Darwin":
        lib_name = "libpykustomize.dylib"
        platform_dir = f"darwin-{machine}"
    elif system == "Windows":
        lib_name = "pykustomize.dll"
        platform_dir = f"windows-{machine}"
    else:
        return None

    # Search in package directory first
    package_dir = Path(__file__).parent
    lib_dir = package_dir / "_lib" / platform_dir
    lib_path = lib_dir / lib_name

    if lib_path.exists():
        return str(lib_path)

    # Search in development location (go build output)
    dev_lib_path = package_dir.parent / "go" / "pykustomize" / "_lib" / platform_dir / lib_name
    if dev_lib_path.exists():
        return str(dev_lib_path)

    return None


def get_library():
    """Get the loaded Kustomize library, loading it if necessary."""
    global _library

    with _library_lock:
        if _library is not None:
            return _library

        lib_path = _find_library()
        if lib_path is None:
            raise KustomizeLibraryNotFound(
                "Could not find pykustomize shared library. Please ensure pykustomize is properly installed."
            )

        try:
            _library = ffi.dlopen(lib_path)
        except OSError as e:
            raise KustomizeLibraryNotFound(
                f"Failed to load pykustomize library from {lib_path}: {e}"
            ) from e

        return _library


def get_version() -> str:
    """Get the version string from the native library."""
    lib = get_library()
    version_ptr = lib.pykustomize_version_string()
    if version_ptr == ffi.NULL:
        return "unknown"
    return ffi.string(version_ptr).decode("utf-8")


def string_from_c(c_str) -> str:
    """Convert a C string to Python string and free it."""
    if c_str == ffi.NULL:
        return ""
    try:
        s = ffi.string(c_str).decode("utf-8")
        return s
    finally:
        lib = get_library()
        lib.pykustomize_free(c_str)


def check_error(result: int) -> None:
    """Check if a C function returned an error and raise an exception if so."""
    if result != 0:
        lib = get_library()
        err_ptr = lib.pykustomize_last_error()
        if err_ptr != ffi.NULL:
            err_msg = ffi.string(err_ptr).decode("utf-8")
            raise KustomizeError(err_msg)
        else:
            raise KustomizeError("Unknown error occurred")


def _reset_for_tests() -> None:
    """Reset library state for testing. Internal use only."""
    global _library, _library_path
    with _library_lock:
        _library = None
        _library_path = None
