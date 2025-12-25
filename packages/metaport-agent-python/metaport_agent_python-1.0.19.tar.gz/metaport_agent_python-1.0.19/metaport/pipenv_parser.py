#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Pipenv parsing module for Metaport Python Agent.

This module parses Pipenv configuration files (Pipfile and Pipfile.lock)
and extracts package information, handling Pipenv-specific dependency formats
and metadata.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import json
import sys

# Import toml for parsing Pipfile files
try:
    import toml
except ImportError:
    print("Error: toml package is required for Pipenv support", file=sys.stderr)
    sys.exit(1)

# Import Package class from requirements_parser
try:
    from .requirements_parser import Package
except ImportError:
    from requirements_parser import Package


class PipenvParser(object):
    """
    Parser for Pipenv configuration files.

    Handles parsing of Pipfile and Pipfile.lock files to extract
    dependency information from Pipenv-managed Python projects.

    Supported files:
        - Pipfile: Pipenv project configuration with dependencies (TOML format)
        - Pipfile.lock: Pipenv lock file with exact versions and metadata (JSON format)
    """

    def __init__(self):
        # type: () -> None
        """Initialize the Pipenv parser."""
        self._parsed_packages = []  # type: List[Package]
        self._parse_errors = []  # type: List[str]

    def parse_pipfile(self, file_path):
        # type: (str) -> List[Package]
        """
        Parse a Pipfile and extract dependency information.

        Reads and parses a Pipenv Pipfile, extracting package dependencies
        from the [packages] and [dev-packages] sections.

        Args:
            file_path: Path to the Pipfile

        Returns:
            List of Package objects representing discovered dependencies
        """
        self._parsed_packages = []
        self._parse_errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except IOError as e:
            error_msg = "Could not read Pipfile {}: {}".format(file_path, str(e))
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except toml.TomlDecodeError as e:
            error_msg = "Could not parse Pipfile {}: {}".format(file_path, str(e))
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    data = toml.load(f)
            except (IOError, toml.TomlDecodeError, UnicodeDecodeError) as e:
                error_msg = "Could not read Pipfile {}: {}".format(file_path, str(e))
                self._parse_errors.append(error_msg)
                print("Error: " + error_msg, file=sys.stderr)
                return []

        # Extract dependencies from Pipfile
        packages = self.extract_dependencies(data)

        # Set source file for all packages
        for package in packages:
            package.source = file_path

        self._parsed_packages = packages
        return packages

    def parse_pipfile_lock(self, file_path):
        # type: (str) -> List[Package]
        """
        Parse a Pipfile.lock file and extract exact dependency information.

        Reads and parses a Pipenv lock file, which contains exact versions
        and metadata for all dependencies including transitive ones.

        Args:
            file_path: Path to the Pipfile.lock file

        Returns:
            List of Package objects with exact version information
        """
        self._parsed_packages = []
        self._parse_errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except IOError as e:
            error_msg = "Could not read Pipfile.lock {}: {}".format(file_path, str(e))
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except json.JSONDecodeError as e:
            error_msg = "Could not parse Pipfile.lock {}: {}".format(file_path, str(e))
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    data = json.load(f)
            except (IOError, json.JSONDecodeError, UnicodeDecodeError) as e:
                error_msg = "Could not read Pipfile.lock {}: {}".format(
                    file_path, str(e)
                )
                self._parse_errors.append(error_msg)
                print("Error: " + error_msg, file=sys.stderr)
                return []

        # Extract packages from lock file
        packages = self._extract_lock_packages(data)

        # Set source file for all packages
        for package in packages:
            package.source = file_path

        self._parsed_packages = packages
        return packages

    def extract_dependencies(self, data):
        # type: (Dict[str, Any]) -> List[Package]
        """
        Extract dependency information from parsed Pipfile data.

        Processes the Pipfile structure to extract package dependencies
        from [packages] and [dev-packages] sections.

        Args:
            data: Parsed TOML data from Pipfile

        Returns:
            List of Package objects representing dependencies
        """
        packages = []

        # Extract main dependencies from [packages] section
        if "packages" in data:
            deps = data["packages"]
            packages.extend(self._parse_dependency_section(deps, "main"))

        # Extract development dependencies from [dev-packages] section
        if "dev-packages" in data:
            dev_deps = data["dev-packages"]
            packages.extend(self._parse_dependency_section(dev_deps, "dev"))

        return packages

    def _parse_dependency_section(self, dependencies, section_name):
        # type: (Dict[str, Any], str) -> List[Package]
        """
        Parse a dependencies section from Pipfile.

        Args:
            dependencies: Dictionary of dependency specifications
            section_name: Name of the section (main, dev, etc.)

        Returns:
            List of Package objects
        """
        packages = []

        for dep_name, dep_spec in dependencies.items():
            package = self._parse_pipenv_dependency(dep_name, dep_spec)
            if package:
                packages.append(package)

        return packages

    def _parse_pipenv_dependency(self, name, spec):
        # type: (str, Any) -> Optional[Package]
        """
        Parse a single Pipenv dependency specification.

        Handles various Pipenv dependency formats including version strings,
        dictionaries with constraints, and VCS/path dependencies.

        Args:
            name: Package name
            spec: Dependency specification (string or dict)

        Returns:
            Package object or None if parsing fails
        """
        # Normalize package name
        normalized_name = name.lower().replace("_", "-")

        if isinstance(spec, str):
            # Simple version specification: "*", ">=1.0.0", "==2.0.0", etc.
            version = self._extract_pipenv_version(spec)
            return Package(name=normalized_name, version=version)

        elif isinstance(spec, dict):
            # Complex specification with version, extras, VCS, etc.
            version = "unknown"

            if "version" in spec:
                version = self._extract_pipenv_version(spec["version"])
            elif "git" in spec:
                # Git dependency
                version = "git+" + spec["git"]
                if "ref" in spec:
                    version += "@" + spec["ref"]
                elif "tag" in spec:
                    version += "@" + spec["tag"]
                elif "branch" in spec:
                    version += "@" + spec["branch"]
            elif "hg" in spec:
                # Mercurial dependency
                version = "hg+" + spec["hg"]
                if "ref" in spec:
                    version += "@" + spec["ref"]
            elif "svn" in spec:
                # Subversion dependency
                version = "svn+" + spec["svn"]
            elif "path" in spec:
                # Local path dependency
                version = "path+" + spec["path"]
            elif "file" in spec:
                # File dependency
                version = "file+" + spec["file"]
            elif "editable" in spec and spec["editable"]:
                # Editable dependency
                if "git" in spec:
                    version = "git+" + spec["git"] + "#editable"
                elif "path" in spec:
                    version = "path+" + spec["path"] + "#editable"
                else:
                    version = "editable"

            return Package(name=normalized_name, version=version)

        else:
            # Unknown specification format
            return Package(name=normalized_name, version="unknown")

    def _extract_pipenv_version(self, version_spec):
        # type: (str) -> str
        """
        Return the original Pipenv version specification for constraint analysis.

        Preserves Pipenv-specific version constraints and wildcards so that 
        LockStatus can be properly determined.

        Args:
            version_spec: Pipenv version specification

        Returns:
            Original version specification string
        """
        if not version_spec or not isinstance(version_spec, str):
            return "unknown"

        # Return the original constraint to preserve operator information
        return version_spec.strip()

    def _extract_lock_packages(self, data):
        # type: (Dict[str, Any]) -> List[Package]
        """
        Extract package information from Pipfile.lock file data.

        Args:
            data: Parsed JSON data from Pipfile.lock

        Returns:
            List of Package objects with exact versions
        """
        packages = []

        # Process both default and develop packages
        for section_name in ["default", "develop"]:
            if section_name not in data:
                continue

            section_data = data[section_name]
            if not isinstance(section_data, dict):
                continue

            for package_name, package_info in section_data.items():
                if not isinstance(package_info, dict):
                    continue

                # Normalize package name
                normalized_name = package_name.lower().replace("_", "-")

                # Extract version
                version = package_info.get("version", "unknown")
                if version.startswith("=="):
                    version = version[2:]

                # Extract dependencies if available
                dependencies = []
                if "dependencies" in package_info:
                    deps = package_info["dependencies"]
                    if isinstance(deps, dict):
                        dependencies = list(deps.keys())
                    elif isinstance(deps, list):
                        dependencies = deps

                # Create package object
                package = Package(
                    name=normalized_name, version=version, dependencies=dependencies
                )

                packages.append(package)

        return packages

    def get_parse_errors(self):
        # type: () -> List[str]
        """
        Get any parsing errors that occurred during the last parse operation.

        Returns:
            List of error messages
        """
        return self._parse_errors[:]

    def has_parse_errors(self):
        # type: () -> bool
        """
        Check if any parsing errors occurred.

        Returns:
            True if there were parsing errors, False otherwise
        """
        return len(self._parse_errors) > 0
