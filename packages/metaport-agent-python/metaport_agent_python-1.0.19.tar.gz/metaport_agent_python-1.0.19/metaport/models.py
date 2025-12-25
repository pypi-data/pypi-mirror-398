#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Models module for Metaport Python Agent.

This module handles all the models represented in Metaport SBOM documents' "components" object.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import sys
import os
import platform
import socket
import subprocess


class Runtime:
    """
    Declares all the methods required to satisfy a Metaport-registered application's Runtime-specific
    data-points.
    """

    def name(self) -> str:
        """
        Returns the name of the runtime.

        Returns:
            str: The name of the runtime.
        """
        return "Python"

    def version(self) -> str:
        """
        Returns the version of the runtime.

        Returns:
            str: The version of the runtime.
        """
        return "{}.{}".format(sys.version_info[0], sys.version_info[1])


class Framework:
    """
    Declares all the methods required to satisfy a Metaport-registered application's Framework-specific
    data-points.

    This class identifies Python web frameworks (Django, Flask, Pyramid, Bottle, etc.) by examining
    the parsed packages from requirements.txt, Poetry, and Pipenv dependency files.
    """

    def __init__(self, packages=None):
        # type: (Optional[List[Any]]) -> None
        """
        Initialize the Framework model with parsed packages.

        Args:
            packages: List of Package objects from dependency parsers
        """
        self._packages = packages or []
        self._frameworks_data = self._load_frameworks_data()
        self._detected_framework = None  # type: Optional[Dict[str, str]]
        self._detect_framework()

    def _load_frameworks_data(self):
        # type: () -> Dict[str, List[str]]
        """
        Load the frameworks data from static JSON file.

        Returns a dictionary mapping framework names to their possible package names.
        Similar to the PHP agent's approach.

        Returns:
            Dict mapping framework names to lists of possible package names
        """
        # Static framework data - mapping framework names to their PyPI package names
        # This mirrors the PHP agent's JSON structure but embedded for Python
        frameworks_data = {
            "django": ["django", "Django"],
            "flask": ["flask", "Flask"],
            "pyramid": ["pyramid", "Pyramid"],
            "bottle": ["bottle", "Bottle"],
            "wagtail": ["wagtail", "Wagtail"],
            "django-cms": ["django-cms"],
            "fastapi": ["fastapi", "FastAPI"],
            "tornado": ["tornado", "Tornado"],
            "cherrypy": ["cherrypy", "CherryPy"],
            "web2py": ["web2py", "Web2py"],
            "falcon": ["falcon", "Falcon"],
            "sanic": ["sanic", "Sanic"],
            "quart": ["quart", "Quart"],
            "starlette": ["starlette", "Starlette"],
            "molten": ["molten"],
            "klein": ["klein"],
            "wheezy": ["wheezy.web"],
            "turbogears": ["turbogears2", "TurboGears2"],
            "pylons": ["pylons", "Pylons"],
        }

        return frameworks_data

    def _detect_framework(self):
        # type: () -> None
        """
        Detect which framework is being used by examining the packages.

        Searches through all parsed packages to find framework matches
        and determines the framework name and version.
        """
        if not self._packages:
            return

        # Create a lookup of package names to Package objects
        package_lookup = {}
        for package in self._packages:
            if hasattr(package, "name") and hasattr(package, "version"):
                # Normalize package name for comparison
                normalized_name = package.name.lower().replace("_", "-")
                package_lookup[normalized_name] = package

        # Search for framework matches
        for framework_name, possible_packages in self._frameworks_data.items():
            for package_name in possible_packages:
                normalized_package = package_name.lower().replace("_", "-")
                if normalized_package in package_lookup:
                    # Found a framework match
                    matched_package = package_lookup[normalized_package]
                    self._detected_framework = {
                        "name": framework_name,
                        "version": matched_package.version,
                        "package_name": matched_package.name,
                    }
                    return

    def name(self):
        # type: () -> Optional[str]
        """
        Returns the name of the detected framework.

        Returns:
            str: The name of the framework, or None if no framework detected
        """
        if self._detected_framework:
            return self._detected_framework["name"]
        return None

    def version(self):
        # type: () -> Optional[str]
        """
        Returns the version of the detected framework.

        Returns:
            str: The version of the framework, or None if no framework detected
        """
        if self._detected_framework:
            return self._detected_framework["version"]
        return None

    def package_name(self):
        # type: () -> Optional[str]
        """
        Returns the actual package name of the detected framework.

        Returns:
            str: The package name as found in dependencies, or None if no framework detected
        """
        if self._detected_framework:
            return self._detected_framework["package_name"]
        return None

    def is_detected(self):
        # type: () -> bool
        """
        Check if a framework was detected.

        Returns:
            bool: True if a framework was detected, False otherwise
        """
        return self._detected_framework is not None

    def get_framework_info(self):
        # type: () -> Optional[Dict[str, str]]
        """
        Get complete framework information.

        Returns:
            Dict containing framework name, version, and package name, or None if no framework detected
        """
        return self._detected_framework.copy() if self._detected_framework else None


class Host:
    """
    Declares all the methods required to satisfy a Metaport-registered application's Host-specific
    data-points.

    This class gathers system information about the host machine including OS, hostname,
    memory, CPU, and storage information.
    """

    def __init__(self):
        # type: () -> None
        """Initialize the Host model and gather system information."""
        self._host_info = self._gather_host_info()

    def _gather_host_info(self):
        # type: () -> Dict[str, str]
        """
        Gather host system information.

        Returns:
            Dict containing host system information
        """
        host_info = {}

        # Get hostname
        try:
            host_info["hostname"] = socket.gethostname()
        except Exception:
            host_info["hostname"] = "Unknown"

        # Get platform information
        try:
            host_info["platform"] = platform.machine()
        except Exception:
            host_info["platform"] = "Unknown"

        # Get memory information
        host_info["memory"] = self._get_memory_info()

        # Get CPU information
        host_info["cpus"] = self._get_cpu_info()

        # Get storage information
        storage_info = self._get_storage_info()
        host_info["storagesize"] = storage_info["size"]
        host_info["storagetype"] = storage_info["type"]

        return host_info

    def _get_memory_info(self):
        # type: () -> str
        """
        Get system memory information.

        Returns:
            str: Memory size (e.g., "16G")
        """
        try:
            # Try to read from /proc/meminfo on Linux
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            # Extract memory in KB and convert to GB
                            mem_kb = int(line.split()[1])
                            mem_gb = round(mem_kb / (1024 * 1024))
                            return "{}G".format(mem_gb)

            # Fallback: try using system commands
            try:
                # Try free command on Linux
                result = subprocess.check_output(
                    ["free", "-h"], universal_newlines=True
                )
                lines = result.strip().split("\n")
                if len(lines) > 1:
                    mem_line = lines[1].split()
                    if len(mem_line) > 1:
                        return mem_line[1]  # Total memory
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            # Try sysctl on macOS
            try:
                result = subprocess.check_output(
                    ["sysctl", "hw.memsize"], universal_newlines=True
                )
                mem_bytes = int(result.split(":")[1].strip())
                mem_gb = round(mem_bytes / (1024 * 1024 * 1024))
                return "{}G".format(mem_gb)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        except Exception:
            pass

        return "Unknown"

    def _get_cpu_info(self):
        # type: () -> str
        """
        Get CPU core count information.

        Returns:
            str: Number of CPU cores
        """
        try:
            # Try to get CPU count
            cpu_count = os.cpu_count()
            if cpu_count:
                return str(cpu_count)
        except Exception:
            pass

        try:
            # Fallback: try reading from /proc/cpuinfo on Linux
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    cpu_count = 0
                    for line in f:
                        if line.startswith("processor"):
                            cpu_count += 1
                    if cpu_count > 0:
                        return str(cpu_count)
        except Exception:
            pass

        return "Unknown"

    def _get_storage_info(self):
        # type: () -> Dict[str, str]
        """
        Get storage information.

        Returns:
            Dict with 'size' and 'type' keys
        """
        storage_info = {"size": "Unknown", "type": "Unknown"}

        try:
            # Try to get disk usage for root filesystem
            if hasattr(os, "statvfs"):
                # Unix-like systems
                statvfs = os.statvfs("/")
                # Calculate total size in GB
                total_size = (statvfs.f_frsize * statvfs.f_blocks) / (
                    1024 * 1024 * 1024
                )
                storage_info["size"] = "{}G".format(int(total_size))

            # Try to get storage device type on Linux
            try:
                # Try to read from lsblk command
                result = subprocess.check_output(
                    ["lsblk", "-d", "-o", "NAME,MODEL"], universal_newlines=True
                )
                lines = result.strip().split("\n")
                if len(lines) > 1:
                    # Get the first disk's model
                    disk_line = lines[1].split(None, 1)
                    if len(disk_line) > 1:
                        storage_info["type"] = disk_line[1].strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            # Fallback: try to read from /sys/block on Linux
            if storage_info["type"] == "Unknown":
                try:
                    block_devices = os.listdir("/sys/block")
                    for device in block_devices:
                        if device.startswith(("sd", "nvme", "hd")):
                            model_path = "/sys/block/{}/device/model".format(device)
                            if os.path.exists(model_path):
                                with open(model_path, "r") as f:
                                    storage_info["type"] = f.read().strip()
                                    break
                except Exception:
                    pass

        except Exception:
            pass

        return storage_info

    def name(self):
        # type: () -> str
        """
        Returns the operating system name.

        Returns:
            str: The OS name
        """
        try:
            # Get OS name
            system = platform.system()
            if system == "Linux":
                # Try to get Linux distribution name
                try:
                    with open("/etc/os-release", "r") as f:
                        for line in f:
                            if line.startswith("NAME="):
                                name = line.split("=")[1].strip().strip('"')
                                return name
                except Exception:
                    pass
                return "Linux"
            elif system == "Darwin":
                return "macOS"
            elif system == "Windows":
                return "Windows"
            else:
                return system
        except Exception:
            return "Unknown"

    def version(self):
        # type: () -> str
        """
        Returns the operating system version.

        Returns:
            str: The OS version
        """
        try:
            system = platform.system()
            if system == "Linux":
                # Try to get Linux distribution version
                try:
                    with open("/etc/os-release", "r") as f:
                        for line in f:
                            if line.startswith("VERSION_ID="):
                                version = line.split("=")[1].strip().strip('"')
                                return version
                except Exception:
                    pass
                return platform.release()
            elif system == "Darwin":
                return platform.mac_ver()[0]
            elif system == "Windows":
                return platform.version()
            else:
                return platform.release()
        except Exception:
            return "Unknown"

    def get_properties(self):
        # type: () -> List[Dict[str, str]]
        """
        Get host properties in the format expected by Metaport SBOM.

        Returns:
            List of property dictionaries with 'name' and 'value' keys
        """
        properties = []

        for key, value in self._host_info.items():
            properties.append({"name": key, "value": value})

        return properties

    def get_host_info(self):
        # type: () -> Dict[str, str]
        """
        Get complete host information.

        Returns:
            Dict containing all host information
        """
        return self._host_info.copy()
