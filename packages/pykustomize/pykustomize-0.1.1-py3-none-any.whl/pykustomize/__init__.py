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

"""Python bindings for Kustomize - Kubernetes configuration customization."""

from importlib.metadata import version as _get_version

from ._ffi import get_version
from .build import (
    BuildOptions,
    BuildResult,
    BuildResultJson,
    Kustomizer,
    LoadRestrictions,
    ReorderOption,
    build,
    build_json,
)
from .exceptions import (
    KustomizeBuildError,
    KustomizeConfigError,
    KustomizeError,
    KustomizeHelmError,
    KustomizeLibraryNotFound,
    KustomizePathError,
    KustomizePluginError,
)

try:
    __version__ = _get_version("pykustomize")
except Exception:
    __version__ = "0.1.0"


def native_version() -> str:
    """Get the version of the native kustomize library."""
    return get_version()


__all__ = [
    # Version
    "__version__",
    "native_version",
    # Main classes
    "Kustomizer",
    "BuildOptions",
    "BuildResult",
    "BuildResultJson",
    # Enums
    "LoadRestrictions",
    "ReorderOption",
    # Convenience functions
    "build",
    "build_json",
    # Exceptions
    "KustomizeError",
    "KustomizeLibraryNotFound",
    "KustomizeBuildError",
    "KustomizeConfigError",
    "KustomizePathError",
    "KustomizePluginError",
    "KustomizeHelmError",
]
