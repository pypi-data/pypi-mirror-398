#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Dependency scanning module for Metaport Python Agent.

This module discovers and identifies Python dependency files in projects,
supporting both traditional requirements.txt files and modern Poetry
configurations (pyproject.toml and poetry.lock).

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import os
import sys


class DependencyFile(object):
    """
    Represents a discovered dependency file.

    Contains information about a dependency file found during project scanning,
    including its path, type, and content for later parsing.

    Attributes:
        path: File system path to the dependency file
        type: Type of dependency file (requirements, poetry_toml, poetry_lock, pipenv_file, pipenv_lock)
        content: Raw file content as string
        packages: List of parsed packages (populated by parsers)
    """

    def __init__(self, path, file_type, content):
        # type: (str, str, str) -> None
        """
        Initialize a dependency file object.

        Args:
            path: File system path to the dependency file
            file_type: Type identifier (requirements, poetry_toml, poetry_lock, pipenv_file, pipenv_lock)
            content: Raw file content as string
        """
        self.path = path
        self.type = file_type
        self.content = content
        self.packages = []  # type: List[Any]


class DependencyScanner(object):
    """
    Scanner for discovering Python dependency files in projects.

    Provides functionality to discover and read dependency files from Python
    projects, supporting both requirements.txt and Poetry-based configurations.
    Handles mixed dependency management scenarios where both formats exist.

    Supported file types:
        - requirements.txt (and variants like requirements-dev.txt)
        - pyproject.toml (Poetry configuration)
        - poetry.lock (Poetry lock file)
        - Pipfile (Pipenv configuration)
        - Pipfile.lock (Pipenv lock file)
    """

    def __init__(self):
        # type: () -> None
        """Initialize the dependency scanner."""
        self._project_path = None  # type: Optional[str]
        self._discovered_files = []  # type: List[DependencyFile]

    def scan_project(self, path=None):
        # type: (Optional[str]) -> List[DependencyFile]
        """
        Scan a Python project for dependency files.

        Discovers all supported dependency files in the specified project
        directory, including requirements.txt files, Poetry configurations,
        and Pipenv configurations.

        Args:
            path: Project directory path. If None, uses current directory.

        Returns:
            List of DependencyFile objects representing discovered files
        """
        if path is None:
            path = os.getcwd()

        self._project_path = os.path.abspath(path)
        self._discovered_files = []

        if not os.path.exists(self._project_path):
            print(
                "Error: Project path does not exist: {}".format(self._project_path),
                file=sys.stderr,
            )
            return []

        if not os.path.isdir(self._project_path):
            print(
                "Error: Project path is not a directory: {}".format(self._project_path),
                file=sys.stderr,
            )
            return []

        # Discover requirements.txt files
        requirements_files = self.find_requirements_files()
        for req_file in requirements_files:
            self._add_dependency_file(req_file, "requirements")

        # Discover Poetry files
        poetry_toml = self.find_poetry_files()
        if poetry_toml:
            self._add_dependency_file(poetry_toml, "poetry_toml")

        # Discover Pipenv files
        pipfile = self.find_pipenv_files()
        if pipfile:
            self._add_dependency_file(pipfile, "pipenv_file")

        return self._discovered_files

    def find_requirements_files(self):
        # type: () -> List[str]
        """
        Find requirements.txt files in the project directory.

        Searches for requirements.txt and common variants like requirements-dev.txt,
        requirements-test.txt, etc. Only searches in the project root directory
        to avoid picking up nested project dependencies.

        Returns:
            List of file paths to requirements.txt files
        """
        if not self._project_path:
            return []

        requirements_files = []

        # Common requirements.txt file patterns
        patterns = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-test.txt",
            "requirements-prod.txt",
            "requirements-production.txt",
            "dev-requirements.txt",
            "test-requirements.txt",
        ]

        for pattern in patterns:
            file_path = os.path.join(self._project_path, pattern)
            if os.path.isfile(file_path):
                requirements_files.append(file_path)

        return requirements_files

    def find_poetry_files(self):
        # type: () -> str
        """
        Find Poetry configuration files in the project directory.

        Searches for pyproject.toml files in the project root.

        Returns:
            A string representing the path to pyproject.toml, or None if not found.
        """
        if not self._project_path:
            return None, None

        pyproject_path = os.path.join(self._project_path, "pyproject.toml")
        pyproject_toml = pyproject_path if os.path.isfile(pyproject_path) else None

        return pyproject_toml

    def find_pipenv_files(self):
        # type: () -> str
        """
        Find Pipenv configuration files in the project directory.

        Searches for Pipfile and Pipfile.lock files in the project root.
        Both files are part of Pipenv's dependency management system.

        Returns:
            A string representing the path to a pipfile, or None if not found.
        """
        if not self._project_path:
            return None, None

        pipfile_path = os.path.join(self._project_path, "Pipfile")
        pipfile = pipfile_path if os.path.isfile(pipfile_path) else None

        return pipfile

    def detect_project_type(self):
        # type: () -> str
        """
        Determine the project's dependency management type.

        Analyzes discovered dependency files to classify the project as using
        requirements.txt, Poetry, Pipenv, or a mixed approach.

        Returns:
            Project type string: 'requirements', 'poetry', 'pipenv', 'mixed', or 'unknown'
        """
        has_requirements = any(f.type == "requirements" for f in self._discovered_files)
        has_poetry = any(f.type in ["poetry_toml"] for f in self._discovered_files)
        has_pipenv = any(f.type in ["pipenv_file"] for f in self._discovered_files)

        # Count how many different types we have
        type_count = sum([has_requirements, has_poetry, has_pipenv])

        if type_count > 1:
            return "mixed"
        elif has_poetry:
            return "poetry"
        elif has_pipenv:
            return "pipenv"
        elif has_requirements:
            return "requirements"
        else:
            return "unknown"

    def _add_dependency_file(self, file_path, file_type):
        # type: (str, str) -> None
        """
        Add a discovered dependency file to the internal list.

        Reads the file content and creates a DependencyFile object for later
        processing by the appropriate parser.

        Args:
            file_path: Path to the dependency file
            file_type: Type identifier for the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            dep_file = DependencyFile(file_path, file_type, content)
            self._discovered_files.append(dep_file)

        except IOError as e:
            print(
                "Warning: Could not read dependency file {}: {}".format(
                    file_path, str(e)
                ),
                file=sys.stderr,
            )
        except UnicodeDecodeError:
            # Try with different encoding for older files
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

                dep_file = DependencyFile(file_path, file_type, content)
                self._discovered_files.append(dep_file)

            except (IOError, UnicodeDecodeError) as e2:
                print(
                    "Warning: Could not read dependency file {}: {}".format(
                        file_path, str(e2)
                    ),
                    file=sys.stderr,
                )

    def get_discovered_files(self):
        # type: () -> List[DependencyFile]
        """
        Get the list of discovered dependency files.

        Returns:
            List of DependencyFile objects from the last scan
        """
        return self._discovered_files[:]

    def get_project_path(self):
        # type: () -> Optional[str]
        """
        Get the current project path being scanned.

        Returns:
            Project directory path or None if not set
        """
        return self._project_path

    def has_requirements_files(self):
        # type: () -> bool
        """
        Check if any requirements.txt files were discovered.

        Returns:
            True if requirements.txt files were found, False otherwise
        """
        return any(f.type == "requirements" for f in self._discovered_files)

    def has_poetry_files(self):
        # type: () -> bool
        """
        Check if any Poetry files were discovered.

        Returns:
            True if Poetry files (pyproject.toml or poetry.lock) were found, False otherwise
        """
        return any(f.type in ["poetry_toml"] for f in self._discovered_files)

    def has_pipenv_files(self):
        # type: () -> bool
        """
        Check if any Pipenv files were discovered.

        Returns:
            True if Pipenv files (Pipfile or Pipfile.lock) were found, False otherwise
        """
        return any(f.type in ["pipenv_file"] for f in self._discovered_files)

    def get_requirements_files(self):
        # type: () -> List[DependencyFile]
        """
        Get all discovered requirements.txt files.

        Returns:
            List of DependencyFile objects for requirements.txt files
        """
        return [f for f in self._discovered_files if f.type == "requirements"]

    def get_poetry_files(self):
        # type: () -> List[DependencyFile]
        """
        Get all discovered Poetry files.

        Returns:
            List of DependencyFile objects for Poetry files (pyproject.toml and poetry.lock)
        """
        return [f for f in self._discovered_files if f.type in ["poetry_toml"]]

    def get_pipenv_files(self):
        # type: () -> List[DependencyFile]
        """
        Get all discovered Pipenv files.

        Returns:
            List of DependencyFile objects for Pipenv files (Pipfile and Pipfile.lock)
        """
        return [f for f in self._discovered_files if f.type in ["pipenv_file"]]
