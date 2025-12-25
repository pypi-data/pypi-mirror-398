#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

SBOM generation module for Metaport Python Agent.

This module generates Software Bill of Materials (SBOM) documents in version 1.4
format using the official CycloneDX Python library, ensuring compatibility with
existing Metaport infrastructure and proper SBOM structure.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import json
import sys
import os
from uuid import UUID
from datetime import datetime
from datetime import UTC

# Import CycloneDX library components
try:
    from cyclonedx.model.bom import Bom
    from cyclonedx.model.component import Component, ComponentType
    from cyclonedx.model import ExternalReference, ExternalReferenceType, Property
    from cyclonedx.output.json import JsonV1Dot4
    from packageurl import PackageURL
except ImportError as e:
    print(
        "Error: cyclonedx-bom package is required for SBOM generation: {}".format(
            str(e)
        ),
        file=sys.stderr,
    )
    sys.exit(1)

# Import Package class from requirements_parser and models
try:
    from .models import Runtime, Framework, Host
    from .ssl_utils import SSLCertificateInfo
    from .vulnerability_scanner import VulnerabilityScanner
except ImportError:
    from models import Runtime, Framework, Host
    from ssl_utils import SSLCertificateInfo
    from vulnerability_scanner import VulnerabilityScanner


class SBOMGenerator(object):
    """
    Generator for SBOM v1.4 compliant documents using CycloneDX library.

    Creates Software Bill of Materials documents following the SBOM specification
    version 1.4 using the official CycloneDX Python library, maintaining
    compatibility with existing Metaport infrastructure.

    The generated SBOM includes:
        - Document metadata and creation information
        - Component list with package details
        - Dependency relationships between components
        - Required Metaport properties for agent identification
    """

    AGENT_NAME = "Python/All"

    def __init__(self):
        # type: () -> None
        """Initialize the SBOM generator."""
        self._generated_bom = None  # type: Optional[Bom]

    def generate_sbom(self, packages, metadata=None):
        # type: (List[Package], Optional[Dict[str, str]]) -> Dict[str, Any]
        """
        Generate a complete SBOM v1.4 document from package list using CycloneDX library.

        Creates a comprehensive SBOM document including metadata, components,
        and relationships, following the SBOM v1.4 specification format.

        Args:
            packages: List of Package objects to include in SBOM
            metadata: Optional metadata dict with application information

        Returns:
            Dict containing complete SBOM document structure
        """

        if metadata is None:
            metadata = {}

        # Create main application component if metadata provided
        main_component = None
        if metadata:
            # Get SSL certificate information for the domain
            ssl_info = self._get_ssl_certificate_info(metadata.get("domain", ""))

            main_component = Component(
                bom_ref=metadata.get("uuid", "main-component"),
                type=ComponentType.APPLICATION,
                name=metadata.get("name", "unknown"),
                version=metadata.get("version", "unknown"),
                properties=[
                    Property(
                        name="metaport.model.type", value=ComponentType.APPLICATION
                    ),
                    Property(
                        name="metaport.release.date",
                        value=datetime.now(UTC).strftime("%Y-%m-%d"),
                    ),
                    Property(
                        name="metaport.release.version",
                        value=metadata.get("version", "unknown"),
                    ),
                    Property(
                        name="metaport.release.env",
                        value=metadata.get("env", "unknown"),
                    ),
                    Property(
                        name="metaport.ssl.domain",
                        value=metadata.get("domain", "unknown"),
                    ),
                    Property(name="metaport.ssl.expiry", value=ssl_info["expiry"]),
                    Property(name="metaport.ssl.issuer", value=ssl_info["issuer"]),
                    Property(name="metaport.report.source", value=self._get_source()),
                ],
            )

        # Create BOM with main component
        bom = Bom()
        if main_component:
            bom.metadata.component = main_component

        bom.serial_number = UUID(metadata.get("uuid", "main-component"))
        bom.version = 1
        bom.metadata.properties.add(
            Property(name="metaport.report.agentname", value=self.AGENT_NAME)
        )
        deps = []
        vulns = []

        # Add Runtime and Framework model components to the BOM
        self._add_model_components(bom, packages)

        # Scan for vulnerabilities using available tools
        vulnerability_scanner = VulnerabilityScanner()
        scanned_vulnerabilities = vulnerability_scanner.scan_vulnerabilities(".")

        # Process packages into Metaport "dependencies" and "vulnerabilities"
        for package in packages:
            dep = self.create_dependency(package)
            if dep:
                deps.append(dep)

        # Add scanned vulnerabilities to the vulnerabilities list
        for vuln_data in scanned_vulnerabilities:
            vulns.append(vuln_data)

        properties = json.dumps({"dependencies": deps, "vulnerabilities": vulns})

        if properties:
            bom.metadata.properties.add(
                Property(name="metaport.report.agentoutput", value=properties)
            )

        # Store the generated BOM
        self._generated_bom = bom

        # Convert to JSON dict using CycloneDX JsonV1Dot4 output
        json_output = JsonV1Dot4(bom)
        sbom_json_str = json_output.output_as_string()
        sbom_dict = json.loads(sbom_json_str)

        return sbom_dict

    def _get_source(self):
        """
        Get the source for this agent's data: CRON or CI.

        Returns:
            String
        """

        return "CI" if os.getenv("MP_IS_CI") else "CRON"

    def _get_ssl_certificate_info(self, domain):
        # type: (str) -> Dict[str, str]
        """
        Get SSL certificate information for the specified domain.

        Retrieves SSL certificate expiry date and issuer information by
        connecting to the domain's HTTPS endpoint.

        Args:
            domain: Domain name to check for SSL certificate info

        Returns:
            Dict containing 'expiry' and 'issuer' keys with certificate info
        """      
        if not domain or domain == "unknown" or not os.getenv("MP_ENABLE_DOMAIN"):
            return {"expiry": "", "issuer": ""}

        try:
            ssl_util = SSLCertificateInfo(timeout=10)
            cert_info = ssl_util.get_certificate_info(domain)
            return cert_info

        except Exception as e:
            print(
                "Warning: Failed to retrieve SSL certificate info for {}: {}".format(
                    domain, str(e)
                ),
                file=sys.stderr,
            )
            return {"expiry": "", "issuer": ""}

    def _get_lock_status(self, version_constraint):
        # type: (str) -> str
        """
        Determine lock status for installed packages.

        Since we now query actual installed packages (not dependency declarations),
        all packages have exact installed versions and should be marked as "LOCKED".
        This matches the behavior of PHP and Node.js agents.

        Args:
            version_constraint: Exact version of installed package

        Returns:
            "LOCKED" for all installed packages, "" for unknown versions
        """
        if not version_constraint or version_constraint == "unknown":
            return ""

        # All installed packages have exact versions, so they're always LOCKED
        return "LOCKED"

    def _add_model_components(self, bom, packages):
        # type: (Bom, List[Package]) -> None
        """
        Add Runtime, Framework, and Host model components to the SBOM.

        Creates components for Runtime, Framework, and Host models and adds them
        to the BOM's components array as required by Metaport.

        Args:
            bom: The CycloneDX BOM object to add components to
            packages: List of parsed packages for framework detection
        """
        # Add Runtime component
        runtime = Runtime()
        runtime_component = Component(
            bom_ref="runtime-python",
            type=ComponentType.LIBRARY,
            name=runtime.name(),
            version=runtime.version(),
        )
        bom.components.add(runtime_component)

        # Add Framework component if detected
        framework = Framework(packages)
        if framework.is_detected():
            framework_component = Component(
                bom_ref="framework-{}".format(framework.name()),
                type=ComponentType.FRAMEWORK,
                name=framework.name(),
                version=framework.version(),
            )
            bom.components.add(framework_component)

        # Add Host component
        host = Host()
        host_properties = []
        for prop in host.get_properties():
            host_properties.append(Property(name=prop["name"], value=prop["value"]))

        host_component = Component(
            bom_ref="host-{}".format(host.name().lower().replace(" ", "-")),
            type=ComponentType.OPERATING_SYSTEM,
            name=host.name(),
            version=host.version(),
            properties=host_properties,
        )
        bom.components.add(host_component)

    def create_dependency(self, package):
        # type: (Package) -> Dict[str, str]
        return {
            "Name": package.name,
            "Version": package.version,
            "Description": "unknown",
            "Author": "unknown",
            "Location": "unknown",
            "LockStatus": getattr(package, "lock_status", "UNKNOWN"),
        }

    def create_vulnerability(self, package):
        # type: (Package) -> Optional[Dict[str, str]]
        """
        Create vulnerability information for a package.

        This method is now deprecated in favor of using the VulnerabilityScanner
        to get real vulnerability data. It returns None to indicate no
        vulnerability information is available for individual packages.

        Args:
            package: Package object

        Returns:
            None (vulnerabilities are now handled by VulnerabilityScanner)
        """
        return None

    def create_component(self, package):
        # type: (Package) -> Optional[Component]
        """
        Create a CycloneDX Component from a Package object.

        Converts package information into CycloneDX Component format,
        including all relevant metadata and identifiers.

        Args:
            package: Package object to convert

        Returns:
            CycloneDX Component object or None if invalid
        """
        if not package or not package.name:
            return None

        try:
            # Create PackageURL for the component
            purl = PackageURL(
                type="pypi",
                name=package.name,
                version=package.version if package.version != "unknown" else None,
            )

            # Create component
            component = Component(
                name=package.name,
                version=package.version if package.version != "unknown" else None,
                type=ComponentType.LIBRARY,
                purl=purl,
                bom_ref=str(purl),
            )

            # Add external reference to PyPI
            pypi_ref = ExternalReference(
                type=ExternalReferenceType.DISTRIBUTION,
                url="https://pypi.org/project/{}/".format(package.name),
            )
            component.external_references.add(pypi_ref)

            # Add required Metaport properties
            # This is where we add the agentname property that Metaport expects
            metaport_agent_property = Property(
                name="metaport.report.agentname", value="Python/All"
            )
            component.properties.add(metaport_agent_property)

            # Add source information if available
            if package.source:
                source_property = Property(name="metaport:source", value=package.source)
                component.properties.add(source_property)

            return component

        except Exception as e:
            print(
                "Warning: Could not create component for package {}: {}".format(
                    package.name, str(e)
                ),
                file=sys.stderr,
            )
            return None

    def validate_sbom(self, sbom):
        # type: (Dict[str, Any]) -> bool
        """
        Validate SBOM document structure and required fields.

        Performs basic validation to ensure the SBOM document contains
        all required fields and follows the expected structure.

        Args:
            sbom: SBOM document to validate

        Returns:
            True if SBOM is valid, False otherwise
        """
        if not isinstance(sbom, dict):
            return False

        # Check required top-level fields for CycloneDX v1.4
        required_fields = ["bomFormat", "specVersion", "serialNumber", "version"]
        for field in required_fields:
            if field not in sbom:
                print(
                    "Error: Missing required SBOM field: {}".format(field),
                    file=sys.stderr,
                )
                return False

        # Validate bomFormat
        if sbom.get("bomFormat") != "CycloneDX":
            print("Error: Invalid bomFormat, expected 'CycloneDX'", file=sys.stderr)
            return False

        # Validate specVersion for v1.4
        if sbom.get("specVersion") != "1.4":
            print("Error: Invalid specVersion, expected '1.4'", file=sys.stderr)
            return False

        # Validate components structure
        if "components" in sbom:
            if not isinstance(sbom["components"], list):
                print("Error: Components must be a list", file=sys.stderr)
                return False

            for component in sbom["components"]:
                if not self._validate_component(component):
                    return False

        return True

    def _validate_component(self, component):
        # type: (Dict[str, Any]) -> bool
        """
        Validate a single SBOM component.

        Args:
            component: Component dict to validate

        Returns:
            True if component is valid, False otherwise
        """
        if not isinstance(component, dict):
            return False

        # Check required component fields for CycloneDX v1.4
        required_fields = ["type", "bom-ref", "name"]
        for field in required_fields:
            if field not in component:
                print(
                    "Error: Missing required component field: {}".format(field),
                    file=sys.stderr,
                )
                return False

        return True

    def get_generated_sbom(self):
        # type: () -> Dict[str, Any]
        """
        Get the last generated SBOM document.

        Returns:
            Dict containing SBOM document or empty dict if none generated
        """
        if self._generated_bom:
            json_output = JsonV1Dot4(self._generated_bom)
            sbom_json_str = json_output.output_as_string()
            return json.loads(sbom_json_str)
        return {}

    def export_sbom_json(self, sbom, file_path):
        # type: (Dict[str, Any], str) -> bool
        """
        Export SBOM document to JSON file.

        Args:
            sbom: SBOM document to export
            file_path: Output file path

        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sbom, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(
                "Error: Could not write SBOM file {}: {}".format(file_path, str(e)),
                file=sys.stderr,
            )
            return False
