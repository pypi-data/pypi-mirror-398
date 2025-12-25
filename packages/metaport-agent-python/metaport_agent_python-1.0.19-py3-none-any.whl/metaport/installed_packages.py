#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Installed packages inspection module for Metaport Python Agent.

This module queries the actual installed packages from the filesystem,
similar to how PHP (vendor/) and Node.js (node_modules/) agents work.
This eliminates the need for deduplication and provides exact installed versions.

Supports Python 3.9+ with appropriate type hints and error handling.
"""

import sys
import subprocess
import json

# Import Package class
try:
    from .requirements_parser import Package
except ImportError:
    from requirements_parser import Package


class InstalledPackageInspector(object):
    """
    Inspector for actual installed packages in the Python environment.

    Queries the filesystem and Python package metadata to get the exact
    installed packages and versions, similar to how PHP and Node.js agents
    work with vendor/ and node_modules/ directories.

    Features:
        - Queries actual installed packages (not dependency declarations)
        - Gets exact versions (always LOCKED status)
        - No deduplication needed (single source of truth)
        - Works with virtual environments and system packages
        - Compatible with pip, poetry, pipenv installed packages
    """

    def __init__(self):
        # type: () -> None
        """Initialize the installed package inspector."""
        self._packages_cache = None  # type: Optional[List[Package]]

    def get_installed_packages(self):
        # type: () -> List[Package]
        """
        Get all installed packages in the current Python environment.

        Queries the actual installed packages using pip list, which provides
        the definitive source of truth for what's actually installed,
        regardless of how they were installed (pip, poetry, pipenv, etc.).

        Returns:
            List of Package objects with exact installed versions
        """
        if self._packages_cache is not None:
            return self._packages_cache

        try:
            # Use pip list --format=json to get installed packages
            # This is the most reliable way to get actual installed packages
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(
                    "Warning: Failed to get installed packages via pip list",
                    file=sys.stderr,
                )
                return self._fallback_get_packages()

            # Parse JSON output
            pip_data = json.loads(result.stdout)
            packages = []

            for item in pip_data:
                name = item.get("name", "")
                version = item.get("version", "unknown")

                if name and version != "unknown":
                    # Create package with exact installed version
                    package = Package(
                        name=name.lower().replace("_", "-"),  # Normalize name
                        version=version,
                        source="installed",  # Mark as installed package
                    )
                    packages.append(package)

            # Filter out common system/build packages that aren't user dependencies
            filtered_packages = self._filter_system_packages(packages)

            self._packages_cache = filtered_packages
            return filtered_packages

        except subprocess.TimeoutExpired:
            print("Warning: pip list command timed out", file=sys.stderr)
            return self._fallback_get_packages()
        except json.JSONDecodeError as e:
            print(
                "Warning: Failed to parse pip list output: {}".format(str(e)),
                file=sys.stderr,
            )
            return self._fallback_get_packages()
        except Exception as e:
            print(
                "Warning: Error getting installed packages: {}".format(str(e)),
                file=sys.stderr,
            )
            return self._fallback_get_packages()

    def _fallback_get_packages(self):
        # type: () -> List[Package]
        """
        Fallback method using importlib.metadata when pip list fails.

        Returns:
            List of Package objects from importlib.metadata
        """
        try:
            # Use importlib.metadata (Python 3.8+) or importlib_metadata
            try:
                from importlib import metadata
            except ImportError:
                import importlib_metadata as metadata

            packages = []

            # Get all installed distributions
            for dist in metadata.distributions():
                name = dist.metadata.get("Name", "")
                version = dist.version

                if name and version:
                    package = Package(
                        name=name.lower().replace("_", "-"),
                        version=version,
                        source="installed",
                    )
                    packages.append(package)

            # Filter system packages
            filtered_packages = self._filter_system_packages(packages)
            return filtered_packages

        except Exception as e:
            print(
                "Warning: Fallback package detection failed: {}".format(str(e)),
                file=sys.stderr,
            )
            return []

    def _filter_system_packages(self, packages):
        # type: (List[Package]) -> List[Package]
        """
        Filter out common system/build packages that aren't user dependencies.

        Removes packages that are typically part of the build system or
        Python infrastructure rather than actual application dependencies.

        Args:
            packages: List of all installed packages

        Returns:
            List of filtered packages (user dependencies only)
        """
        # Common system packages to exclude (similar to how npm excludes certain packages)
        system_packages = {
            "pip",
            "setuptools",
            "wheel",
            "pip-tools",
            "virtualenv",
            "pipenv",
            "poetry",
            "poetry-core",
            "build",
            "twine",
            "pytest",
            "pytest-cov",
            "coverage",
            "flake8",
            "black",
            "mypy",
            "isort",
            "pre-commit",
            "tox",
            "sphinx",
            "setuptools-scm",
            "versioneer",
            "bumpversion",
        }

        filtered = []
        for package in packages:
            # Keep packages that aren't in the system packages list
            if package.name not in system_packages:
                filtered.append(package)

        return filtered

    def get_package_info(self, package_name):
        # type: (str) -> Optional[Package]
        """
        Get information about a specific installed package.

        Args:
            package_name: Name of the package to look up

        Returns:
            Package object if found, None otherwise
        """
        packages = self.get_installed_packages()

        # Normalize package name for comparison
        normalized_name = package_name.lower().replace("_", "-")

        for package in packages:
            if package.name == normalized_name:
                return package

        return None

    def is_package_installed(self, package_name):
        # type: (str) -> bool
        """
        Check if a specific package is installed.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is installed, False otherwise
        """
        return self.get_package_info(package_name) is not None

    def get_package_count(self):
        # type: () -> int
        """
        Get the total number of installed packages.

        Returns:
            Number of installed packages
        """
        return len(self.get_installed_packages())

    def clear_cache(self):
        # type: () -> None
        """
        Clear the internal package cache.

        Forces the next call to get_installed_packages() to re-scan
        the installed packages.
        """
        self._packages_cache = None
