#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Main orchestration module for Metaport Python Agent.

This module serves as the main executable entry point and orchestrates
the complete SBOM generation and transport process, coordinating all
components to provide the same functionality as the PHP and Node.js agents.

Supports Python + with appropriate type hints and error handling.
"""

import os
import sys

# Import all required components using relative imports
from .cli import parse_arguments, validate_arguments
from .config_manager import ConfigManager
from .dependency_scanner import DependencyScanner
from .requirements_parser import RequirementsParser
from .poetry_parser import PoetryParser
from .pipenv_parser import PipenvParser
from .installed_packages import InstalledPackageInspector
from .sbom_generator import SBOMGenerator
from .https_transport import HTTPSTransport
from .email_transport import EmailTransport

class Metaport(object):
    """
    Main Metaport agent orchestration class.
    
    Coordinates the complete SBOM generation and transport workflow,
    managing all components and ensuring proper error handling and
    exit codes throughout the process.
    
    This class serves as the main executable entry point when the
    metaport.py file is run directly, providing the same interface
    and functionality as the PHP and Node.js Metaport agents.
    """
    
    def __init__(self):
        # type: () -> None
        """Initialize the Metaport agent."""
        self._config_manager = None  # type: Optional[ConfigManager]
        self._scanner = None  # type: Optional[DependencyScanner]
        self._sbom_generator = None  # type: Optional[SBOMGenerator]
        self._transport = None  # type: Optional[Any]
        self._initialized = False
        self._project_path = None  # type: Optional[str]
    
    def main(self):
        # type: () -> int
        """
        Main entry point for direct execution.
        
        This method is called when the metaport.py file is executed directly,
        providing the same command-line interface as the PHP and Node.js agents.
        
        Returns:
            Exit code (0 for success, >0 for errors)
            
        Example:
            $ ./metaport/metaport.py --transport=http --name=myapp ...
        """
        try:
            # Check Python version compatibility
            if not self._check_python_version():
                return 1
            
            # Parse and validate command-line arguments
            args = parse_arguments()
            if not validate_arguments(args):
                return 1
            
            # Execute the main workflow
            return self.execute(args)
        
        except KeyboardInterrupt:
            print("Error: Operation interrupted by user", file=sys.stderr)
            return 1
        except Exception as e:
            print("Error: Unexpected error: {}".format(str(e)), file=sys.stderr)
            return 1
        finally:
            # Ensure cleanup is performed
            self.cleanup()
    
    def execute(self, args=None):
        # type: (Optional[Any]) -> int
        """
        Execute the main SBOM generation and transport workflow.
        
        Orchestrates the complete process from dependency scanning through
        SBOM generation to final transport, handling errors and ensuring
        proper exit codes.
        
        Args:
            args: Parsed command-line arguments (optional)
            
        Returns:
            Exit code (0 for success, >0 for errors)
        """
        try:
            # Initialize all components
            if not self.initialize(args):
                return 1
            
            # Set project path (current directory by default)
            self._project_path = os.getcwd()
            
            # Step 1: Scan for dependency files
            dependency_files = self._scan_dependencies()
            if not dependency_files:
                print("Info: No dependency files found in project - this is legitimate for projects with no dependencies", file=sys.stderr)
            
            # Step 2: Parse dependencies
            packages = self._parse_dependencies(dependency_files)
            if not packages:
                print("Info: No packages found in dependency files - this is legitimate for projects with no dependencies", file=sys.stderr)
            
            # Step 3: Generate SBOM document
            sbom = self._generate_sbom(packages)
            if not sbom:
                print("Error: Failed to generate SBOM document", file=sys.stderr)
                return 1
            
            # Step 4: Handle SBOM retention if configured
            if not self._handle_sbom_retention(sbom):
                # Continue even if retention fails (non-critical)
                pass
            
            # Step 5: Transport SBOM to Metaport instance
            if not self._transport_sbom(sbom):
                print("Error: Failed to transport SBOM document", file=sys.stderr)
                return 1
            
            # Success
            return 0
        
        except Exception as e:
            print("Error: Execution failed: {}".format(str(e)), file=sys.stderr)
            return 1
    
    def initialize(self, args=None):
        # type: (Optional[Any]) -> bool
        """
        Initialize all components and validate configuration.
        
        Sets up the configuration manager, dependency scanner, SBOM generator,
        and transport components based on the provided arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize configuration manager
            self._config_manager = ConfigManager()
            self._config_manager.load_config(args)
            
            if not self._config_manager.validate_config():
                return False
            
            # Initialize dependency scanner
            self._scanner = DependencyScanner()
            
            # Initialize SBOM generator
            self._sbom_generator = SBOMGenerator()
            
            # Initialize transport based on configuration
            transport_type = self._config_manager.get_config_value('transport', '')
            transport_config = self._config_manager.get_transport_config()
            
            if transport_type == 'http':
                self._transport = HTTPSTransport(transport_config)
            elif transport_type == 'email':
                self._transport = EmailTransport(transport_config)
            else:
                print("Error: Invalid transport type: {}".format(transport_type), file=sys.stderr)
                return False
            
            self._initialized = True
            return True
        
        except Exception as e:
            print("Error: Initialization failed: {}".format(str(e)), file=sys.stderr)
            return False
    
    def _scan_dependencies(self):
        # type: () -> List[Any]
        """
        Scan project for dependency files.
        
        Returns:
            List of discovered dependency files
        """
        if not self._scanner:
            return []
        
        try:
            return self._scanner.scan_project(self._project_path)
        
        except Exception as e:
            print("Error: Dependency scanning failed: {}".format(str(e)), file=sys.stderr)
            return []
    
    def _parse_dependencies(self, dependency_files):
        # type: (List[Any]) -> List[Package]
        """
        Get actual installed packages with proper LockStatus determination.
        
        This method:
        1. Parses dependency files to identify direct dependencies and their constraints
        2. Gets actual installed packages from the environment
        3. Cross-references to determine LockStatus for each package:
           - LOCKED: Direct dependencies with exact versions
           - RANGE: Direct dependencies with version ranges  
           - UNKNOWN: Transitive dependencies (not directly declared)
        
        Args:
            dependency_files: List of DependencyFile objects
            
        Returns:
            List of Package objects with proper LockStatus
        """
        try:
            # Parse dependency files to get direct dependencies and their constraints
            direct_dependencies = self._parse_direct_dependencies(dependency_files)
            inspector = InstalledPackageInspector()
            installed_packages = inspector.get_installed_packages()
            
            if not installed_packages:
                print("Warning: No installed packages found in environment", file=sys.stderr)
                return []
            
            final_packages = []
            for installed_pkg in installed_packages:
                # Check if this package is a direct dependency
                direct_constraint = direct_dependencies.get(installed_pkg.name)
                
                if direct_constraint:
                    # This is a direct dependency - determine LockStatus from constraint
                    lock_status = self._determine_lock_status_from_constraint(direct_constraint)
                    installed_pkg.lock_status = lock_status
                else:
                    # This is a transitive dependency
                    installed_pkg.lock_status = 'UNKNOWN'
                
                final_packages.append(installed_pkg)
            
            return final_packages
        
        except Exception as e:
            print("Error: Failed to parse dependencies: {}".format(str(e)), file=sys.stderr)
            return []
    
    def _parse_direct_dependencies(self, dependency_files):
        # type: (List[Any]) -> Dict[str, str]
        """
        Parse dependency files to extract direct dependencies and their constraints.
        
        Args:
            dependency_files: List of DependencyFile objects
            
        Returns:
            Dict mapping package names to their version constraints
        """
        direct_deps = {}  # type: Dict[str, str]
        
        try:
            requirements_parser = RequirementsParser()
            poetry_parser = PoetryParser()
            pipenv_parser = PipenvParser()
            
            for dep_file in dependency_files:
                packages = []
                
                if dep_file.type == 'requirements':
                    packages = requirements_parser.parse_requirements(dep_file.path)
                elif dep_file.type == 'poetry_toml':
                    packages = poetry_parser.parse_pyproject_toml(dep_file.path)
                elif dep_file.type == 'pipenv_file':
                    packages = pipenv_parser.parse_pipfile(dep_file.path)
                
                # Extract constraints from parsed packages
                for package in packages:
                    if package.name and package.version:
                        # Store the constraint (not the resolved version)
                        direct_deps[package.name] = package.version
            
            return direct_deps
        
        except Exception as e:
            print("Warning: Failed to parse direct dependencies: {}".format(str(e)), file=sys.stderr)
            return {}
    
    def _determine_lock_status_from_constraint(self, constraint):
        # type: (str) -> str
        """
        Determine LockStatus based on version constraint format.
        
        Args:
            constraint: Version constraint string from dependency file
            
        Returns:
            "LOCKED" for exact versions, "RANGE" for version ranges
        """
        if not constraint or constraint == 'unknown':
            return 'UNKNOWN'
        
        import re
        
        # RANGE: Look for range indicators (simplified approach)
        # Check for common range indicators: ^, ~, *, <, >, !, (, or wildcard patterns
        if any(char in constraint for char in ['^', '~', '*', '<', '>', '!', '(']):
            return 'RANGE'
        
        # LOCKED: Exact version with == operator or plain version number
        if re.match(r'^(==|\d+)', constraint):
            return 'LOCKED'
        
        return 'UNKNOWN'
    
    def _generate_sbom(self, packages):
        # type: (List[Package]) -> Optional[Dict[str, Any]]
        """
        Generate SBOM document from packages.
        
        Args:
            packages: List of Package objects
            
        Returns:
            SBOM document dict or None if generation fails
        """
        if not self._sbom_generator or not self._config_manager:
            return None
        
        try:
            # Prepare metadata for SBOM generation
            config = self._config_manager.get_config()
            metadata = {
                'name': config.get('name', ''),
                'version': config.get('version', ''),
                'uuid': config.get('uuid', ''),
                'domain': config.get('domain', ''),
                'env': config.get('env', ''),
                'host': config.get('host', ''),
                'classic': config.get('classic', False)
            }
            
            # Generate SBOM
            sbom = self._sbom_generator.generate_sbom(packages, metadata)
            
            # Validate SBOM
            if not self._sbom_generator.validate_sbom(sbom):
                return None
            
            return sbom
        
        except Exception:
            return None
    
    def _handle_sbom_retention(self, sbom):
        # type: (Dict[str, Any]) -> bool
        """
        Handle SBOM retention if MP_RETAIN_SBOM is enabled.
        
        Args:
            sbom: SBOM document to potentially retain
            
        Returns:
            True if retention handled successfully (or not needed), False on error
        """
        if not self._config_manager:
            return True
        
        try:
            retain_sbom = self._config_manager.get_config_value('retain_sbom', False)
            
            if retain_sbom and self._sbom_generator:
                filename = 'sbom.json'
                
                if not self._sbom_generator.export_sbom_json(sbom, filename):
                    return False
            
            return True
        
        except Exception as e:
            print("Warning: SBOM retention failed: {}".format(str(e)), file=sys.stderr)
            return False
    
    def _transport_sbom(self, sbom):
        # type: (Dict[str, Any]) -> bool
        """
        Transport SBOM document to Metaport instance.
        
        Args:
            sbom: SBOM document to transport
            
        Returns:
            True if transport successful, False otherwise
        """
        if not self._transport or not self._config_manager:
            return False
        
        try:
            # Prepare metadata for transport
            config = self._config_manager.get_config()
            metadata = {
                'name': config.get('name', ''),
                'version': config.get('version', ''),
                'uuid': config.get('uuid', ''),
                'domain': config.get('domain', ''),
                'env': config.get('env', ''),
                'host': config.get('host', ''),
                'classic': config.get('classic', False),
                'transport': config.get('transport', ''),
                'auth': config.get('auth', '')
            }
            
            # Send SBOM
            return self._transport.send(sbom, metadata)
    
        except Exception as e:
            print("Error: SBOM transport failed: {}".format(str(e)), file=sys.stderr)
            return False

    
    def _check_python_version(self):
        # type: () -> bool
        """
        Check if Python version meets minimum requirements.
        
        Returns:
            True if Python version is supported, False otherwise
        """
        if sys.version_info < (3, 9):
            print("Error: Python  or higher is required", file=sys.stderr)
            print("Current version: {}.{}.{}".format(
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro
            ), file=sys.stderr)
            return False
        
        return True
    
    def cleanup(self):
        # type: () -> None
        """
        Clean up resources and temporary files.
        
        Performs cleanup of transport connections, temporary files,
        and other resources used during execution.
        """
        try:
            if self._transport and hasattr(self._transport, 'cleanup'):
                self._transport.cleanup()
        except Exception:
            # Ignore cleanup errors
            pass
        
        # Reset state
        self._initialized = False
        self._transport = None


def main():
    # type: () -> int
    """
    Main entry point for command-line execution.
    
    This function is called when the module is executed directly or via
    the console script entry point defined in setup.py.
    
    Returns:
        Exit code (0 for success, >0 for errors)
    """
    agent = Metaport()
    return agent.main()


# Allow direct execution of this module
if __name__ == '__main__':
    sys.exit(main())
