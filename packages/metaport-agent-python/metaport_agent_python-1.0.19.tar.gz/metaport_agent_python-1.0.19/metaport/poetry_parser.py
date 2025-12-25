#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

pyproject.toml parsing module for Metaport Python Agent.

This module parses pyproject.toml files and extracts package information,
supporting both Poetry format ([tool.poetry]) and modern PEP 621 format
([project]) dependency specifications, as well as poetry.lock files.

Supports Python 10+ with appropriate type hints and error handling.
"""

import sys

# Import toml for parsing pyproject.toml files
try:
    import toml
except ImportError:
    print("Error: toml package is required for Poetry support", file=sys.stderr)
    sys.exit(1)

# Import Package class from requirements_parser
try:
    from .requirements_parser import Package
except ImportError:
    from requirements_parser import Package


class PoetryParser(object):
    """
    Parser for pyproject.toml configuration files.

    Handles parsing of pyproject.toml and poetry.lock files to extract
    dependency information from both Poetry-managed projects and modern
    PEP 621 format projects.

    Supported files:
        - pyproject.toml: Poetry format ([tool.poetry]) or PEP 621 format ([project])
        - poetry.lock: Poetry lock file with exact versions and metadata

    Supported formats:
        - Poetry format: [tool.poetry.dependencies] sections
        - PEP 621 format: [project] dependencies and optional-dependencies
    """

    def __init__(self):
        # type: () -> None
        """Initialize the Poetry parser."""
        self._parsed_packages = []  # type: List[Package]
        self._parse_errors = []  # type: List[str]

    def parse_pyproject_toml(self, file_path):
        # type: (str) -> List[Package]
        """
        Parse a pyproject.toml file and extract dependency information.

        Reads and parses a pyproject.toml file, supporting both Poetry format
        ([tool.poetry.dependencies]) and modern PEP 621 format ([project])
        dependency specifications.

        Args:
            file_path: Path to the pyproject.toml file

        Returns:
            List of Package objects representing discovered dependencies
        """
        self._parsed_packages = []
        self._parse_errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except IOError as e:
            error_msg = "Could not read pyproject.toml file {}: {}".format(
                file_path, str(e)
            )
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except toml.TomlDecodeError as e:
            error_msg = "Could not parse pyproject.toml file {}: {}".format(
                file_path, str(e)
            )
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    data = toml.load(f)
            except (IOError, toml.TomlDecodeError, UnicodeDecodeError) as e:
                error_msg = "Could not read pyproject.toml file {}: {}".format(
                    file_path, str(e)
                )
                self._parse_errors.append(error_msg)
                print("Error: " + error_msg, file=sys.stderr)
                return []

        # Extract dependencies from Poetry configuration
        packages = self.extract_dependencies(data)

        # Set source file for all packages
        for package in packages:
            package.source = file_path

        self._parsed_packages = packages
        return packages

    def parse_poetry_lock(self, file_path):
        # type: (str) -> List[Package]
        """
        Parse a poetry.lock file and extract exact dependency information.

        Reads and parses a Poetry lock file, which contains exact versions
        and metadata for all dependencies including transitive ones.

        Args:
            file_path: Path to the poetry.lock file

        Returns:
            List of Package objects with exact version information
        """
        self._parsed_packages = []
        self._parse_errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except IOError as e:
            error_msg = "Could not read poetry.lock file {}: {}".format(
                file_path, str(e)
            )
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except toml.TomlDecodeError as e:
            error_msg = "Could not parse poetry.lock file {}: {}".format(
                file_path, str(e)
            )
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    data = toml.load(f)
            except (IOError, toml.TomlDecodeError, UnicodeDecodeError) as e:
                error_msg = "Could not read poetry.lock file {}: {}".format(
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
        Extract dependency information from parsed pyproject.toml data.

        Processes the Poetry configuration structure to extract package
        dependencies from various sections.

        Args:
            data: Parsed TOML data from pyproject.toml

        Returns:
            List of Package objects representing dependencies
        """
        packages = []

        # Check if this is a Poetry project
        if "tool" in data and "poetry" in data["tool"]:
            poetry_config = data["tool"]["poetry"]

            # Extract main dependencies
            if "dependencies" in poetry_config:
                deps = poetry_config["dependencies"]
                packages.extend(self._parse_dependency_section(deps, "main"))

            # Extract development dependencies
            if "dev-dependencies" in poetry_config:
                dev_deps = poetry_config["dev-dependencies"]
                packages.extend(self._parse_dependency_section(dev_deps, "dev"))

            # Extract group dependencies (Poetry 1.2+)
            if "group" in poetry_config:
                groups = poetry_config["group"]
                for group_name, group_config in groups.items():
                    if "dependencies" in group_config:
                        group_deps = group_config["dependencies"]
                        packages.extend(
                            self._parse_dependency_section(group_deps, group_name)
                        )

        # Also check for modern PEP 621 format [project] dependencies
        if "project" in data:
            project_config = data["project"]

            # Extract main dependencies from [project] section
            if "dependencies" in project_config:
                deps = project_config["dependencies"]
                packages.extend(self._parse_pep621_dependencies(deps, "main"))

            # Extract optional dependencies from [project.optional-dependencies]
            if "optional-dependencies" in project_config:
                optional_deps = project_config["optional-dependencies"]
                for group_name, group_deps in optional_deps.items():
                    packages.extend(
                        self._parse_pep621_dependencies(group_deps, group_name)
                    )

        return packages

    def _parse_pep621_dependencies(self, dependencies, section_name):
        # type: (List[str], str) -> List[Package]
        """
        Parse PEP 621 format dependencies from [project] section.

        PEP 621 dependencies are specified as a list of requirement strings,
        similar to requirements.txt format.

        Args:
            dependencies: List of dependency strings (e.g., ["requests>=2.20.0", "toml>=0.10.0"])
            section_name: Name of the dependency section (e.g., 'main', 'dev')

        Returns:
            List of Package objects
        """
        packages = []

        if not isinstance(dependencies, list):
            return packages

        for dep_str in dependencies:
            if not isinstance(dep_str, str):
                continue

            try:
                # Parse requirement string (similar to requirements.txt format)
                # Handle formats like: "requests>=2.20.0", "toml", "black>=18.9b0; python_version>='3.6'"

                # Split on semicolon to separate package spec from markers
                parts = dep_str.split(";", 1)
                package_spec = parts[0].strip()

                if not package_spec:
                    continue

                # Parse package name and version constraint
                name, version = self._parse_package_spec(package_spec)

                if name:
                    package = Package(name, version, section_name)
                    packages.append(package)

            except Exception as e:
                error_msg = "Could not parse PEP 621 dependency '{}': {}".format(
                    dep_str, str(e)
                )
                self._parse_errors.append(error_msg)
                print("Warning: " + error_msg, file=sys.stderr)
                continue

        return packages

    def _parse_package_spec(self, package_spec):
        # type: (str) -> Tuple[str, str]
        """
        Parse a package specification string to extract name and version.

        Handles formats like:
        - "requests" -> ("requests", "unknown")
        - "requests>=2.20.0" -> ("requests", ">=2.20.0")
        - "requests==2.28.1" -> ("requests", "2.28.1")

        Args:
            package_spec: Package specification string

        Returns:
            Tuple of (package_name, version_constraint)
        """
        import re

        # Handle complex constraints with parentheses first
        if "(" in package_spec and ")" in package_spec:
            # Extract package name before the space and parentheses
            parts = package_spec.split(" ", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                constraint = parts[1].strip()
                return name, constraint
        
        # Pattern to match package name and version constraint
        # Supports: ==, >=, <=, >, <, !=, ~=, ===
        pattern = r"^([a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]|[a-zA-Z0-9])(?:\s*([><=!~]+)\s*([^,\s]+))?"

        match = re.match(pattern, package_spec.strip())
        if not match:
            return "", "unknown"

        name = match.group(1)
        operator = match.group(2)
        version = match.group(3)

        if operator and version:
            return name, operator + version
        else:
            return name, "unknown"

    def _parse_dependency_section(self, dependencies, section_name):
        # type: (Dict[str, Any], str) -> List[Package]
        """
        Parse a dependencies section from pyproject.toml.

        Args:
            dependencies: Dictionary of dependency specifications
            section_name: Name of the section (main, dev, etc.)

        Returns:
            List of Package objects
        """
        packages = []

        for dep_name, dep_spec in dependencies.items():
            # Skip Python version requirement
            if dep_name.lower() == "python":
                continue

            package = self._parse_poetry_dependency(dep_name, dep_spec)
            if package:
                packages.append(package)

        return packages

    def _parse_poetry_dependency(self, name, spec):
        # type: (str, Any) -> Optional[Package]
        """
        Parse a single Poetry dependency specification.

        Handles various Poetry dependency formats including version strings,
        dictionaries with constraints, and git/path dependencies.

        Args:
            name: Package name
            spec: Dependency specification (string or dict)

        Returns:
            Package object or None if parsing fails
        """
        # Normalize package name
        normalized_name = name.lower().replace("_", "-")

        if isinstance(spec, str):
            # Simple version specification: "^1.0.0", ">=1.0.0", etc.
            version = self._extract_poetry_version(spec)
            return Package(name=normalized_name, version=version)

        elif isinstance(spec, dict):
            # Complex specification with version, extras, etc.
            version = "unknown"

            if "version" in spec:
                version = self._extract_poetry_version(spec["version"])
            elif "git" in spec:
                # Git dependency
                version = "git+" + spec["git"]
                if "rev" in spec:
                    version += "@" + spec["rev"]
                elif "tag" in spec:
                    version += "@" + spec["tag"]
                elif "branch" in spec:
                    version += "@" + spec["branch"]
            elif "path" in spec:
                # Local path dependency
                version = "path+" + spec["path"]
            elif "url" in spec:
                # URL dependency
                version = "url+" + spec["url"]

            return Package(name=normalized_name, version=version)

        else:
            # Unknown specification format
            return Package(name=normalized_name, version="unknown")

    def _extract_poetry_version(self, version_spec):
        # type: (str) -> str
        """
        Return the original Poetry version specification for constraint analysis.

        Preserves Poetry-specific version constraints like ^1.0.0, ~1.0.0, etc.
        so that LockStatus can be properly determined.

        Args:
            version_spec: Poetry version specification

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
        Extract package information from poetry.lock file data.

        Args:
            data: Parsed TOML data from poetry.lock

        Returns:
            List of Package objects with exact versions
        """
        packages = []

        if "package" not in data:
            return packages

        for package_data in data["package"]:
            if not isinstance(package_data, dict):
                continue

            name = package_data.get("name", "")
            version = package_data.get("version", "unknown")

            if not name:
                continue

            # Normalize package name
            normalized_name = name.lower().replace("_", "-")

            # Extract dependencies if available
            dependencies = []
            if "dependencies" in package_data:
                deps = package_data["dependencies"]
                if isinstance(deps, dict):
                    dependencies = list(deps.keys())

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
