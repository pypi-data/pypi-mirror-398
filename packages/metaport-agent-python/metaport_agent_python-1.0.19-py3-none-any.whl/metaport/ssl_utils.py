#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

SSL certificate utilities for Metaport Python Agent.

This module provides functionality to retrieve SSL certificate information
from domains, including expiry dates and issuer details, following the same
approach as the Node.js agent.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import ssl
import socket
import sys
from datetime import datetime


class SSLCertificateInfo(object):
    """
    SSL certificate information retrieval utility.

    Provides methods to connect to domains and extract SSL certificate
    information including expiry dates and issuer details, matching the
    functionality of the Node.js agent.

    Features:
        - SSL certificate retrieval via HTTPS connection
        - Certificate expiry date extraction
        - Certificate issuer information parsing
        - Error handling for connection failures
        - Timeout handling for slow connections
    """

    def __init__(self, timeout=10):
        # type: (int) -> None
        """
        Initialize SSL certificate info utility.

        Args:
            timeout: Connection timeout in seconds (default: 10)
        """
        self._timeout = timeout

    def get_certificate_info(self, domain, port=443):
        # type: (str, int) -> Dict[str, str]
        """
        Get SSL certificate information for a domain.

        Connects to the specified domain and retrieves SSL certificate
        information including expiry date and issuer details.

        Args:
            domain: Domain name to check (e.g., 'example.com')
            port: Port to connect to (default: 443)

        Returns:
            Dict containing certificate information with keys:
            - 'expiry': Certificate expiry date in ISO format or ''
            - 'issuer': Certificate issuer name or ''
        """
        try:
            # Clean domain name (remove protocol if present)
            domain = self._clean_domain(domain)

            # Get certificate from the domain
            cert = self._get_certificate(domain, port)
            if not cert:
                return self._get_unknown_cert_info()

            # Extract expiry date
            expiry = self._extract_expiry_date(cert)

            # Extract issuer information
            issuer = self._extract_issuer(cert)

            return {"expiry": expiry, "issuer": issuer}

        except Exception as e:
            print(
                "Warning: Could not retrieve SSL certificate info for {}: {}".format(
                    domain, str(e)
                ),
                file=sys.stderr,
            )
            return self._get_unknown_cert_info()

    def _clean_domain(self, domain):
        # type: (str) -> str
        """
        Clean domain name by removing protocol and path components.

        Args:
            domain: Raw domain string that may include protocol

        Returns:
            Clean domain name
        """
        if not domain:
            return domain

        # Remove protocol if present
        if "://" in domain:
            domain = domain.split("://", 1)[1]

        # Remove path if present
        if "/" in domain:
            domain = domain.split("/", 1)[0]

        # Remove port if present (we'll use the port parameter instead)
        if ":" in domain:
            domain = domain.split(":", 1)[0]

        return domain.strip()

    def _get_certificate(self, domain, port):
        # type: (str, int) -> Optional[Dict]
        """
        Retrieve SSL certificate from domain.

        Args:
            domain: Domain name to connect to
            port: Port to connect to

        Returns:
            Certificate dict or None if retrieval fails
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()

            # Connect to the domain and get certificate
            with socket.create_connection(
                (domain, port), timeout=self._timeout
            ) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return cert

        except socket.timeout:
            print(
                "Warning: Timeout connecting to {} on port {}".format(domain, port),
                file=sys.stderr,
            )
            return None
        except socket.gaierror as e:
            print(
                "Warning: DNS resolution failed for {}: {}".format(domain, str(e)),
                file=sys.stderr,
            )
            return None
        except ssl.SSLError as e:
            print(
                "Warning: SSL error connecting to {}: {}".format(domain, str(e)),
                file=sys.stderr,
            )
            return None
        except Exception as e:
            print(
                "Warning: Unexpected error connecting to {}: {}".format(domain, str(e)),
                file=sys.stderr,
            )
            return None

    def _extract_expiry_date(self, cert):
        # type: (Dict) -> str
        """
        Extract expiry date from certificate.

        Args:
            cert: Certificate dict from getpeercert()

        Returns:
            ISO formatted expiry date string or 'unknown'
        """
        try:
            if "notAfter" not in cert:
                return ""

            # Parse the certificate date format: 'MMM DD HH:MM:SS YYYY GMT'
            not_after = cert["notAfter"]

            # Convert to datetime object
            # Certificate dates are in format: 'Dec 31 23:59:59 2024 GMT'
            dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")

            # Convert to ISO format with Z suffix for UTC
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        except (ValueError, KeyError) as e:
            print(
                "Warning: Could not parse certificate expiry date: {}".format(str(e)),
                file=sys.stderr,
            )
            return ""
        except Exception as e:
            print(
                "Warning: Unexpected error parsing expiry date: {}".format(str(e)),
                file=sys.stderr,
            )
            return ""

    def _extract_issuer(self, cert):
        # type: (Dict) -> str
        """
        Extract issuer information from certificate.

        Args:
            cert: Certificate dict from getpeercert()

        Returns:
            Issuer name string or ''
        """
        try:
            if "issuer" not in cert:
                return ""

            issuer_info = cert["issuer"]

            # issuer is a tuple of tuples of tuples: ((('countryName', 'US'),), (('organizationName', 'Google Trust Services'),), ...)
            # Look for common name (CN) or organization name (O)
            issuer_name = ""
            org_name = ""

            for item_group in issuer_info:
                # Each item_group is a tuple containing one tuple with (field_name, field_value)
                if len(item_group) > 0 and len(item_group[0]) >= 2:
                    field_name, field_value = item_group[0][0], item_group[0][1]

                    # Prefer commonName, but also collect organizationName as fallback
                    if field_name == "commonName":
                        issuer_name = field_value
                    elif field_name == "organizationName":
                        org_name = field_value

            # Use commonName if available, otherwise organizationName
            if issuer_name != "":
                return issuer_name
            elif org_name != "":
                return org_name
            else:
                return ""

        except (KeyError, IndexError, TypeError) as e:
            print(
                "Warning: Could not parse certificate issuer: {}".format(str(e)),
                file=sys.stderr,
            )
            return ""
        except Exception as e:
            print(
                "Warning: Unexpected error parsing issuer: {}".format(str(e)),
                file=sys.stderr,
            )
            return ""

    def _get_unknown_cert_info(self):
        # type: () -> Dict[str, str]
        """
        Get default certificate info for unknown/failed cases.

        Returns:
            Dict with empty values for expiry and issuer
        """
        return {"expiry": "", "issuer": ""}

    def test_connection(self, domain, port=443):
        # type: (str, int) -> bool
        """
        Test if SSL connection to domain is possible.

        Args:
            domain: Domain name to test
            port: Port to test (default: 443)

        Returns:
            True if connection successful, False otherwise
        """
        try:
            domain = self._clean_domain(domain)
            cert = self._get_certificate(domain, port)
            return cert is not None
        except Exception:
            return False
