#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Requirements.txt parsing module for Metaport Python Agent.

This module parses requirements.txt files and extracts package information,
handling various requirements.txt formats and edge cases commonly found
in Python projects.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import re
import sys


class Package(object):
    """
    Represents a Python package dependency.

    Contains information about a package including its name, version,
    license information, and dependencies.

    Attributes:
        name: Package name (normalized)
        version: Package version string
        license: Package license information (if available)
        dependencies: List of dependency package names
        source: Source file where this package was discovered
    """

    def __init__(
        self, name, version, license_info=None, dependencies=None, source=None
    ):
        # type: (str, str, Optional[str], Optional[List[str]], Optional[str]) -> None
        """
        Initialize a package object.

        Args:
            name: Package name
            version: Package version string
            license_info: License information (optional)
            dependencies: List of dependency names (optional)
            source: Source file path (optional)
        """
        self.name = name
        self.version = version
        self.license = license_info
        self.dependencies = dependencies if dependencies is not None else []
        self.source = source

    def __repr__(self):
        # type: () -> str
        """String representation of the package."""
        return "Package(name='{}', version='{}', source='{}')".format(
            self.name, self.version, self.source
        )

    def __eq__(self, other):
        # type: (object) -> bool
        """Check equality based on name and version."""
        if not isinstance(other, Package):
            return False
        return self.name == other.name and self.version == other.version


class RequirementsParser(object):
    """
    Parser for requirements.txt files.

    Handles parsing of requirements.txt files with support for various formats
    including version specifiers, comments, and common edge cases found in
    Python projects.

    Supported formats:
        - package==1.0.0
        - package>=1.0.0
        - package~=1.0.0
        - package[extra]==1.0.0
        - -e git+https://github.com/user/repo.git
        - -r other-requirements.txt
        - # comments and blank lines
    """

    def __init__(self):
        # type: () -> None
        """Initialize the requirements parser."""
        self._parsed_packages = []  # type: List[Package]
        self._parse_errors = []  # type: List[str]

    def parse_requirements(self, file_path):
        # type: (str) -> List[Package]
        """
        Parse a requirements.txt file and extract package information.

        Reads and parses a requirements.txt file, extracting package names
        and version information while handling various formats and edge cases.

        Args:
            file_path: Path to the requirements.txt file

        Returns:
            List of Package objects representing discovered dependencies
        """
        self._parsed_packages = []
        self._parse_errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            error_msg = "Could not read requirements file {}: {}".format(
                file_path, str(e)
            )
            self._parse_errors.append(error_msg)
            print("Error: " + error_msg, file=sys.stderr)
            return []
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except (IOError, UnicodeDecodeError) as e:
                error_msg = "Could not read requirements file {}: {}".format(
                    file_path, str(e)
                )
                self._parse_errors.append(error_msg)
                print("Error: " + error_msg, file=sys.stderr)
                return []

        # Parse content line by line
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            package = self.parse_line(line)
            if package:
                package.source = file_path
                self._parsed_packages.append(package)

        return self._parsed_packages

    def parse_line(self, line):
        # type: (str) -> Optional[Package]
        """
        Parse a single line from a requirements.txt file.

        Handles various requirement line formats including version specifiers,
        comments, and special pip options.

        Args:
            line: Single line from requirements.txt file

        Returns:
            Package object if line contains a valid package, None otherwise
        """
        if not line:
            return None

        # Strip whitespace
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return None

        # Skip pip options and includes
        if line.startswith("-"):
            # Skip -r, -e, --find-links, etc.
            return None

        # Handle inline comments
        if "#" in line:
            line = line.split("#")[0].strip()
            if not line:
                return None

        # Parse package specification
        package = self._parse_package_spec(line)
        return package

    def _parse_package_spec(self, spec):
        # type: (str) -> Optional[Package]
        """
        Parse a package specification string.

        Handles various package specification formats including version
        constraints and extras.

        Args:
            spec: Package specification string (e.g., 'requests==2.25.1')

        Returns:
            Package object or None if parsing fails
        """
        # Remove any trailing semicolon and environment markers
        if ";" in spec:
            spec = spec.split(";")[0].strip()

        # Pattern to match package specifications
        # Matches: package_name[extras]==version, package_name>=version, etc.
        pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)(\[[^\]]+\])?(.*)"
        match = re.match(pattern, spec)

        if not match:
            return None

        package_name = match.group(1)
        version_spec = match.group(4)  # ==1.0.0, >=1.0.0, etc.

        if not package_name:
            return None

        # Normalize package name (lowercase, replace underscores with hyphens)
        normalized_name = package_name.lower().replace("_", "-")

        # Store the original constraint, not just the extracted version
        version = version_spec.strip() if version_spec.strip() else "unknown"

        # Create package object
        package = Package(
            name=normalized_name,
            version=version,
            source=None,  # Will be set by caller
        )

        return package

    def _extract_version(self, version_spec):
        # type: (str) -> str
        """
        Extract version number from version specification.

        Handles various version specifiers like ==, >=, ~=, etc.
        and extracts the actual version number.

        Args:
            version_spec: Version specification (e.g., '==2.25.1', '>=1.0.0')

        Returns:
            Version string or 'unknown' if no version found
        """
        if not version_spec:
            return "unknown"

        version_spec = version_spec.strip()

        # Common version specifier patterns
        patterns = [
            r"==\s*([^\s,]+)",  # ==1.0.0
            r">=\s*([^\s,]+)",  # >=1.0.0
            r">\s*([^\s,]+)",  # >1.0.0
            r"<=\s*([^\s,]+)",  # <=1.0.0
            r"<\s*([^\s,]+)",  # <1.0.0
            r"~=\s*([^\s,]+)",  # ~=1.0.0
            r"!=\s*([^\s,]+)",  # !=1.0.0
            r"===\s*([^\s,]+)",  # ===1.0.0
            r"^([0-9][^\s,]*)",  # Direct version number
        ]

        for pattern in patterns:
            match = re.search(pattern, version_spec)
            if match:
                return match.group(1)

        # If no pattern matches, return the spec as-is (cleaned)
        cleaned_spec = re.sub(r"[<>=!~\s]", "", version_spec)
        return cleaned_spec if cleaned_spec else "unknown"

    def resolve_transitive_dependencies(self, packages):
        # type: (List[Package]) -> List[Package]
        """
        Resolve transitive dependencies for the given packages.

        Note: This is a placeholder implementation. Full transitive dependency
        resolution would require querying PyPI or using pip's dependency resolver,
        which is complex and may not be necessary for SBOM generation.

        Args:
            packages: List of direct dependencies

        Returns:
            List of packages including transitive dependencies
        """
        # For now, return the original packages
        # In a full implementation, this would:
        # 1. Query PyPI for each package's dependencies
        # 2. Recursively resolve dependencies
        # 3. Handle version conflicts
        # 4. Return the complete dependency tree

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
