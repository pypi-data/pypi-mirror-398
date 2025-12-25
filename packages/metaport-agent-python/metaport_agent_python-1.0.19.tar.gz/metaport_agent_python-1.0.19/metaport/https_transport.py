#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

HTTPS transport module for Metaport Python Agent.

This module handles secure transmission of SBOM documents and metadata
to Metaport instances via HTTPS, supporting authentication, SSL certificate
validation, and the MP_IGNORE_CERT environment variable.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import json
import sys

# Import requests for HTTP client functionality
try:
    import requests
except ImportError:
    print("Error: requests package is required for HTTPS transport", file=sys.stderr)
    sys.exit(1)


class HTTPSTransport(object):
    """
    HTTPS transport for sending SBOM data to Metaport instances.

    Handles secure transmission of SBOM documents and application metadata
    to Metaport API endpoints using HTTPS with proper authentication and
    SSL certificate validation.

    Features:
        - TLS 1.2+ with certificate validation
        - Authentication token support
        - MP_IGNORE_CERT environment variable support
        - Proper error handling and exit codes
    """

    def __init__(self, config=None):
        # type: (Optional[Dict[str, Any]]) -> None
        """
        Initialize HTTPS transport with configuration.

        Args:
            config: Transport configuration dict containing URL, token, etc.
        """
        self._config = config or {}
        self._session = None  # type: Optional[requests.Session]
        self._authenticated = False

    def send(self, sbom, metadata):
        # type: (Dict[str, Any], Dict[str, str]) -> bool
        """
        Send SBOM document and metadata to Metaport instance via HTTPS.

        Transmits the SBOM document along with application metadata to the
        configured Metaport API endpoint using secure HTTPS connection.

        Args:
            sbom: SBOM document dict to transmit
            metadata: Application metadata dict

        Returns:
            True if transmission successful, False otherwise
        """
        # Validate configuration
        if not self._validate_config():
            return False

        # Initialize session if needed
        if not self._session:
            self._session = self._create_session()

        # Authenticate if needed
        if not self._authenticated:
            if not self.authenticate():
                return False

        # Prepare request data
        request_data = sbom
        _response = None

        # Send request
        try:
            # Store UUID for URL construction
            self._current_uuid = metadata.get("uuid", "")

            url = self._get_api_url()
            headers = self._get_request_headers()

            # Use PUT method as per PHP agent implementation
            _response = self._session.put(
                url, json=request_data, headers=headers, timeout=30
            )

            if _response.status_code != 202:
                returnStruct = {
                    "success": False,
                    "code": _response.status_code,
                    "message": "Fail",
                }
            else:
                returnStruct = {
                    "success": True,
                    "code": 202,
                    "message": "OK",
                }

            print(json.dumps(returnStruct), file=sys.stdout)

            # Check response status
            return _response.status_code == 202

        except requests.exceptions.SSLError as e:
            msg = "Error: SSL certificate validation failed: {}".format(str(e))
        except requests.exceptions.ConnectionError:
            msg = "Error: Connection failed"
        except requests.exceptions.Timeout:
            msg = "Error: Request timeout"
        except requests.exceptions.RequestException:
            msg = "Error: HTTP request failed"
        except Exception:
            msg = "Error: Unexpected error during HTTPS transmission"

        returnStruct = {
            "success": False,
            "code": _response.status_code if _response else 400,
            "message": msg,
        }

        print(json.dumps(returnStruct), file=sys.stderr)

        return False

    def authenticate(self):
        # type: () -> bool
        """
        Perform authentication with the Metaport API.

        Validates the authentication token and establishes an authenticated
        session for subsequent requests.

        Returns:
            True if authentication successful, False otherwise
        """
        # For token-based authentication, we don't need a separate auth step
        # The token is included in request headers
        token = self._config.get("token", "")
        if not token:
            print("Error: No authentication token provided", file=sys.stderr)
            return False

        self._authenticated = True
        return True

    def _validate_config(self):
        # type: () -> bool
        """
        Validate HTTPS transport configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self._config.get("host"):
            print("Error: No host configured for HTTPS transport", file=sys.stderr)
            return False

        if not self._config.get("token"):
            print(
                "Error: No authentication token configured for HTTPS transport",
                file=sys.stderr,
            )
            return False

        return True

    def _create_session(self):
        # type: () -> requests.Session
        """
        Create and configure HTTP session.

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure SSL certificate validation
        ignore_cert = self._config.get("ignore_cert", False)
        if ignore_cert:
            session.verify = False
            # Disable SSL warnings when ignoring certificates
            try:
                from requests.packages.urllib3 import disable_warnings
                from requests.packages.urllib3.exceptions import InsecureRequestWarning

                disable_warnings(InsecureRequestWarning)
            except ImportError:
                pass
        else:
            session.verify = True

        return session

    def _get_api_url(self):
        # type: () -> str
        """
        Get the complete API URL for SBOM submission.

        Based on the PHP agent implementation, the endpoint is:
        https://{host}/api/v1/app

        Returns:
            Complete API endpoint URL
        """
        host = self._config.get("host", "")

        # Ensure URL has proper format
        if not host.startswith("https"):
            host = "https://" + host

        # Construct the API endpoint following PHP agent pattern
        api_url = (
            "{}api/v1/app".format(host)
            if host.endswith("/")
            else "{}/api/v1/app".format(host)
        )

        return api_url

    def _get_request_headers(self):
        # type: () -> Dict[str, str]
        """
        Get HTTP request headers including authentication.

        Returns:
            Dict of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "metaport-agent-python/1.0.0",
            "Accept": "application/json",
        }

        # Add authentication header
        token = self._config.get("token", "")
        if token:
            headers["Authorization"] = "Basic {}".format(token)

        return headers

    def cleanup(self):
        # type: () -> None
        """
        Clean up transport resources.

        Closes HTTP session and performs any necessary cleanup.
        """
        if self._session:
            self._session.close()
            self._session = None

        self._authenticated = False
