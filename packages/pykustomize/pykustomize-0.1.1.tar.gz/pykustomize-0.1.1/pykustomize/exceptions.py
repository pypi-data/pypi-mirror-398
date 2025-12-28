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

"""Exception types for pykustomize."""

from __future__ import annotations


class KustomizeError(Exception):
    """Base exception for all pykustomize errors."""

    pass


class KustomizeLibraryNotFound(KustomizeError):
    """Raised when the native library cannot be found or loaded."""

    pass


class KustomizeBuildError(KustomizeError):
    """Raised when a kustomize build operation fails."""

    pass


class KustomizeConfigError(KustomizeError):
    """Raised when there's a configuration error."""

    pass


class KustomizePathError(KustomizeError):
    """Raised when there's an issue with the kustomization path."""

    pass


class KustomizePluginError(KustomizeError):
    """Raised when there's a plugin-related error."""

    pass


class KustomizeHelmError(KustomizeError):
    """Raised when there's a Helm-related error."""

    pass


__all__ = [
    "KustomizeError",
    "KustomizeLibraryNotFound",
    "KustomizeBuildError",
    "KustomizeConfigError",
    "KustomizePathError",
    "KustomizePluginError",
    "KustomizeHelmError",
]
