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

"""Kustomize build operations."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ._ffi import check_error, ffi, get_library, string_from_c
from .exceptions import KustomizeBuildError, KustomizePathError


class LoadRestrictions(Enum):
    """Controls what files can be loaded during kustomization."""

    ROOT_ONLY = 0
    """Only allow loading files from within the kustomization root (secure default)."""

    NONE = 1
    """Allow loading files from anywhere (less secure, but more flexible)."""


class ReorderOption(Enum):
    """Controls the order of resources in the output."""

    UNSPECIFIED = "unspecified"
    """Let kustomize select the appropriate default."""

    LEGACY = "legacy"
    """Use a fixed order for backwards compatibility."""

    NONE = "none"
    """Respect the depth-first resource input order."""


@dataclass
class BuildOptions:
    """Options for kustomize build operations."""

    load_restrictions: LoadRestrictions = LoadRestrictions.ROOT_ONLY
    """Controls what files can be loaded during kustomization."""

    reorder: ReorderOption = ReorderOption.UNSPECIFIED
    """Controls the order of resources in the output."""

    add_managedby_label: bool = False
    """Add app.kubernetes.io/managed-by label to all resources."""

    enable_plugins: bool = False
    """Enable kustomize plugins."""

    enable_helm: bool = False
    """Enable Helm chart inflation."""

    helm_command: str = ""
    """Path to helm binary (if enable_helm is True)."""

    def to_json(self) -> str:
        """Convert options to JSON for FFI."""
        return json.dumps({
            "load_restrictions": self.load_restrictions.value,
            "reorder": self.reorder.value,
            "add_managedby_label": self.add_managedby_label,
            "enable_plugins": self.enable_plugins,
            "enable_helm": self.enable_helm,
            "helm_command": self.helm_command,
        })


@dataclass
class BuildResult:
    """Result of a kustomize build operation."""

    yaml: str
    """The rendered YAML output."""

    @property
    def documents(self) -> list[str]:
        """Split the YAML into individual documents."""
        return [doc.strip() for doc in self.yaml.split("---") if doc.strip()]


@dataclass
class BuildResultJson:
    """Result of a kustomize build operation with JSON output."""

    resources: list[dict[str, Any]] = field(default_factory=list)
    """List of Kubernetes resources as dictionaries."""

    count: int = 0
    """Number of resources in the result."""


class Kustomizer:
    """Main class for performing kustomize operations.

    This class provides a Pythonic interface to the kustomize Go library.
    All operations are async to support concurrent execution without blocking.

    Example:
        ```python
        from pykustomize import Kustomizer, BuildOptions, LoadRestrictions

        async def main():
            kustomizer = Kustomizer()

            # Simple build
            result = await kustomizer.build("/path/to/kustomization")
            print(result.yaml)

            # Build with options
            options = BuildOptions(
                load_restrictions=LoadRestrictions.NONE,
                add_managedby_label=True,
            )
            result = await kustomizer.build("/path/to/kustomization", options)

            # Build to JSON for programmatic access
            result_json = await kustomizer.build_json("/path/to/kustomization")
            for resource in result_json.resources:
                print(f"{resource['kind']}: {resource['metadata']['name']}")
        ```
    """

    def __init__(self) -> None:
        """Initialize the Kustomizer."""
        self._lib = get_library()

    async def build(
        self,
        path: str | Path,
        options: BuildOptions | None = None,
    ) -> BuildResult:
        """Build a kustomization and return the rendered YAML.

        Args:
            path: Path to the directory containing kustomization.yaml
            options: Build options (uses defaults if not provided)

        Returns:
            BuildResult containing the rendered YAML

        Raises:
            KustomizePathError: If the path doesn't exist
            KustomizeBuildError: If the build fails
        """
        path = Path(path)
        if not path.exists():
            raise KustomizePathError(f"Kustomization path does not exist: {path}")
        if not path.is_dir():
            raise KustomizePathError(f"Kustomization path must be a directory: {path}")

        options = options or BuildOptions()

        def _build() -> str:
            path_c = ffi.new("char[]", str(path).encode("utf-8"))
            options_c = ffi.new("char[]", options.to_json().encode("utf-8"))
            result_ptr = ffi.new("char**")

            ret = self._lib.pykustomize_build(path_c, options_c, result_ptr)
            check_error(ret)

            return string_from_c(result_ptr[0])

        yaml_output = await asyncio.to_thread(_build)
        return BuildResult(yaml=yaml_output)

    async def build_json(
        self,
        path: str | Path,
        options: BuildOptions | None = None,
    ) -> BuildResultJson:
        """Build a kustomization and return the result as JSON.

        This is useful for programmatic access to individual resources.

        Args:
            path: Path to the directory containing kustomization.yaml
            options: Build options (uses defaults if not provided)

        Returns:
            BuildResultJson containing the resources as dictionaries

        Raises:
            KustomizePathError: If the path doesn't exist
            KustomizeBuildError: If the build fails
        """
        path = Path(path)
        if not path.exists():
            raise KustomizePathError(f"Kustomization path does not exist: {path}")
        if not path.is_dir():
            raise KustomizePathError(f"Kustomization path must be a directory: {path}")

        options = options or BuildOptions()

        def _build_json() -> dict[str, Any]:
            path_c = ffi.new("char[]", str(path).encode("utf-8"))
            options_c = ffi.new("char[]", options.to_json().encode("utf-8"))
            result_ptr = ffi.new("char**")

            ret = self._lib.pykustomize_build_to_json(path_c, options_c, result_ptr)
            check_error(ret)

            result_str = string_from_c(result_ptr[0])
            return json.loads(result_str)

        result_dict = await asyncio.to_thread(_build_json)
        return BuildResultJson(
            resources=result_dict.get("resources", []),
            count=result_dict.get("count", 0),
        )

    async def get_builtin_plugins(self) -> list[str]:
        """Get a list of available builtin plugin names.

        Returns:
            List of builtin plugin names
        """
        def _get_plugins() -> list[str]:
            result_ptr = ffi.new("char**")
            ret = self._lib.pykustomize_get_builtin_plugins(result_ptr)
            check_error(ret)
            result_str = string_from_c(result_ptr[0])
            return json.loads(result_str)

        return await asyncio.to_thread(_get_plugins)


# Convenience function for simple builds
async def build(
    path: str | Path,
    options: BuildOptions | None = None,
) -> BuildResult:
    """Build a kustomization and return the rendered YAML.

    This is a convenience function that creates a Kustomizer instance
    and calls build() on it.

    Args:
        path: Path to the directory containing kustomization.yaml
        options: Build options (uses defaults if not provided)

    Returns:
        BuildResult containing the rendered YAML

    Example:
        ```python
        from pykustomize import build

        async def main():
            result = await build("/path/to/kustomization")
            print(result.yaml)
        ```
    """
    kustomizer = Kustomizer()
    return await kustomizer.build(path, options)


async def build_json(
    path: str | Path,
    options: BuildOptions | None = None,
) -> BuildResultJson:
    """Build a kustomization and return the result as JSON.

    This is a convenience function that creates a Kustomizer instance
    and calls build_json() on it.

    Args:
        path: Path to the directory containing kustomization.yaml
        options: Build options (uses defaults if not provided)

    Returns:
        BuildResultJson containing the resources as dictionaries

    Example:
        ```python
        from pykustomize import build_json

        async def main():
            result = await build_json("/path/to/kustomization")
            for resource in result.resources:
                print(f"{resource['kind']}: {resource['metadata']['name']}")
        ```
    """
    kustomizer = Kustomizer()
    return await kustomizer.build_json(path, options)
