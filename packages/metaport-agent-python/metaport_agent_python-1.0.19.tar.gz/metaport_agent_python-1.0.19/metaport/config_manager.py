#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Configuration management module for Metaport Python Agent.

This module handles environment variable processing and configuration validation,
using the exact same environment variable names and handling logic as the
PHP and Node.js Metaport agents.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import os
import sys


class ConfigManager(object):
    """
    Configuration manager for Metaport agent settings.

    Handles loading and validation of configuration from environment variables
    and command-line arguments, maintaining consistency with PHP and Node.js agents.

    Environment Variables (matching other agents):
        METAPORT_API_URL: Metaport instance URL for HTTPS transport
        METAPORT_API_TOKEN: Authentication token for API access
        MAILER_DSN: Email DSN for email transport (smtp://user:pass@host:port)
        MP_MAIL_TRANSPORT_PUBKEY: Encryption key for email attachment encryption
        MP_IGNORE_CERT: Ignore SSL certificate validation (0|1)
        MP_RETAIN_SBOM: Retain SBOM files locally after transmission (0|1)
    """

    def __init__(self):
        # type: () -> None
        """Initialize the configuration manager."""
        self._config = {}  # type: Dict[str, Any]
        self._loaded = False

    def load_config(self, cli_args=None):
        # type: (Optional[Any]) -> Dict[str, Any]
        """
        Load and merge configuration from environment variables and CLI arguments.

        Processes environment variables using the same names and logic as the
        PHP and Node.js agents, then merges with command-line arguments.

        Args:
            cli_args: Parsed command-line arguments from argparse

        Returns:
            Dict containing merged configuration settings
        """
        # Start with environment variables
        env_config = self._load_environment_variables()

        # Merge with CLI arguments if provided
        if cli_args:
            cli_config = self._extract_cli_config(cli_args)
            env_config.update(cli_config)

        self._config = env_config
        self._loaded = True

        return self._config

    def _load_environment_variables(self):
        # type: () -> Dict[str, Any]
        """
        Load configuration from environment variables.

        Uses the exact same environment variable names as PHP and Node.js agents
        to ensure consistent configuration across all agent implementations.

        Returns:
            Dict containing environment variable configuration
        """
        config = {}

        # API configuration for HTTPS transport
        api_url = self.get_environment_variable("METAPORT_API_URL")
        if api_url:
            config["api_url"] = api_url

        api_token = self.get_environment_variable("METAPORT_API_TOKEN")
        if api_token:
            config["api_token"] = api_token

        # Email configuration for email transport - parse from MAILER_DSN
        mailer_dsn = self.get_environment_variable("MAILER_DSN")
        if mailer_dsn:
            dsn_config = self.unpack_mailer_dsn(mailer_dsn)
            if dsn_config:
                config.update(dsn_config)

        # Encryption configuration
        encrypt_key = self.get_environment_variable("MP_MAIL_TRANSPORT_PUBKEY")
        if encrypt_key:
            config["encrypt_key"] = encrypt_key

        # SSL certificate validation configuration
        ignore_cert = self.get_environment_variable("MP_IGNORE_CERT")
        if ignore_cert:
            config["ignore_cert"] = self._parse_boolean_flag(ignore_cert)

        retain_sbom = self.get_environment_variable("MP_RETAIN_SBOM")
        if retain_sbom:
            config["retain_sbom"] = self._parse_boolean_flag(retain_sbom)

        return config

    def unpack_dsn(self, dsn):
        # type: (str) -> Dict[str, str]
        """
        Unpack DSN (Data Source Name) string into its components.

        Args:
            dsn: DSN string

        Returns:
            Dict containing DSN components
        """
        parts = dsn.split("://")
        if len(parts) != 2:
            print("Invalid email DSN", file=sys.stderr)
            return False

        transport = parts[0]
        rest = parts[1].split("@")
        if len(rest) != 2:
            print(
                "Invalid email transport, account or host given in DSN", file=sys.stderr
            )
            return False

        host = rest[1]
        rest = rest[0].split(":")
        if len(rest) != 2:
            print("Invalid email host or port given in DSN", file=sys.stderr)
            return False

        name = rest[0]
        uuid = rest[1].split("?")[0]

        return {
            "transport": transport,
            "name": name,
            "host": host,
            "uuid": uuid,
        }

    def unpack_mailer_dsn(self, dsn):
        # type: (str) -> Optional[Dict[str, str]]
        """
        Unpack MAILER_DSN string into email configuration components.

        Parses DSN format: smtp://username:password@hostname:port

        Args:
            dsn: MAILER_DSN string (e.g., "smtp://someone@company.com:some_password@smtp.domain.com:587")

        Returns:
            Dict containing email configuration or None if parsing fails
        """
        try:
            # Parse the DSN format: smtp://username:password@hostname:port
            if not dsn.startswith("smtp://"):
                print("Error: MAILER_DSN must start with 'smtp://'", file=sys.stderr)
                return None

            # Remove the smtp:// prefix
            dsn_without_scheme = dsn[7:]  # Remove 'smtp://'

            # Split on the last '@' to separate credentials from host
            parts = dsn_without_scheme.rsplit("@", 1)
            if len(parts) != 2:
                print(
                    "Error: Invalid MAILER_DSN format - missing '@' separator",
                    file=sys.stderr,
                )
                return None

            credentials_part = parts[0]
            host_part = parts[1]

            # Parse credentials (username:password)
            if ":" not in credentials_part:
                print(
                    "Error: Invalid MAILER_DSN format - missing ':' in credentials",
                    file=sys.stderr,
                )
                return None

            username, password = credentials_part.split(":", 1)

            # Parse host and port
            if ":" in host_part:
                host, port = host_part.split(":", 1)
                try:
                    port = int(port)
                except ValueError:
                    print("Error: Invalid port number in MAILER_DSN", file=sys.stderr)
                    return None
            else:
                host = host_part
                port = 587  # Default SMTP submission port

            return {
                "email_host": host,
                "email_user": username,
                "email_pass": password,
                "email_port": str(port),
            }

        except Exception as e:
            print(
                "Error: Failed to parse MAILER_DSN: {}".format(str(e)), file=sys.stderr
            )
            return None

    def _extract_cli_config(self, cli_args):
        # type: (Any) -> Dict[str, Any]
        """
        Extract configuration from parsed CLI arguments.

        Args:
            cli_args: Parsed arguments from argparse

        Returns:
            Dict containing CLI configuration
        """
        config = {}

        # Required CLI arguments
        config["transport"] = cli_args.transport
        config["name"] = cli_args.name
        config["host"] = cli_args.host
        config["uuid"] = cli_args.uuid
        config["domain"] = cli_args.domain
        config["env"] = cli_args.env
        config["version"] = cli_args.version
        config["auth"] = cli_args.auth

        # Optional CLI arguments
        if hasattr(cli_args, "classic"):
            config["classic"] = self._parse_boolean_flag(cli_args.classic)

        return config

    def get_environment_variable(self, name):
        # type: (str) -> Optional[str]
        """
        Get environment variable value.

        Provides a consistent interface for accessing environment variables
        with proper handling of missing values.

        Args:
            name: Environment variable name

        Returns:
            Environment variable value or None if not set
        """
        return os.environ.get(name)

    def _parse_boolean_flag(self, value):
        # type: (str) -> bool
        """
        Parse boolean flag from string value.

        Handles the same boolean parsing logic as PHP and Node.js agents,
        treating '1', 'true', 'yes' as True and '0', 'false', 'no' as False.

        Args:
            value: String value to parse

        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower_value = value.lower().strip()
            return lower_value in ["1", "true", "yes", "on"]

        return False

    def validate_config(self):
        # type: () -> bool
        """
        Validate loaded configuration parameters.

        Ensures all required configuration is present and valid for the
        selected transport method and operational mode.

        Returns:
            True if configuration is valid, False otherwise

        Note:
            Prints error messages to stderr for invalid configuration.
            The calling code should exit with non-zero code on validation failure.
        """
        if not self._loaded:
            print("Error: Configuration not loaded", file=sys.stderr)
            return False

        errors = []

        # Validate required CLI parameters
        required_fields = [
            "transport",
            "name",
            "host",
            "uuid",
            "domain",
            "env",
            "version",
            "auth",
        ]

        for field in required_fields:
            if field not in self._config or not self._config[field]:
                errors.append("Missing required parameter: {}".format(field))

        # Validate transport-specific configuration
        if "transport" in self._config:
            transport = self._config["transport"]

            if transport == "http":
                # HTTPS transport validation
                if not self._config.get("host"):
                    errors.append("HTTPS transport requires --host parameter")

                if not self._config.get("auth"):
                    errors.append("HTTPS transport requires --auth parameter")

            elif transport == "email":
                # Email transport validation - requires MAILER_DSN
                if not self._config.get("email_host"):
                    errors.append(
                        "Email transport requires MAILER_DSN environment variable"
                    )

                if not self._config.get("email_user"):
                    errors.append(
                        "Email transport requires valid MAILER_DSN with username"
                    )

                if not self._config.get("email_pass"):
                    errors.append(
                        "Email transport requires valid MAILER_DSN with password"
                    )

                if not self._config.get("encrypt_key"):
                    errors.append(
                        "Email transport requires MP_MAIL_TRANSPORT_PUBKEY environment variable"
                    )

        # Print errors if any
        if errors:
            print("Error: Invalid configuration:", file=sys.stderr)
            for error in errors:
                print("  - " + error, file=sys.stderr)
            return False

        return True

    def get_transport_config(self):
        # type: () -> Dict[str, str]
        """
        Get transport-specific configuration settings.

        Returns configuration parameters relevant to the selected transport method,
        formatted for use by transport classes.

        Returns:
            Dict containing transport-specific configuration
        """
        if not self._loaded:
            return {}

        transport = self._config.get("transport", "")
        transport_config = {}

        if transport == "http":
            # HTTPS transport configuration
            # Use --host argument directly as the host
            transport_config["host"] = self._config.get("host")
            transport_config["token"] = self._config.get(
                "api_token"
            ) or self._config.get("auth")
            transport_config["ignore_cert"] = self._config.get("ignore_cert", False)

        elif transport == "email":
            # Email transport configuration from MAILER_DSN
            transport_config["host"] = self._config.get("email_host", "")
            transport_config["user"] = self._config.get("email_user", "")
            transport_config["pass"] = self._config.get("email_pass", "")
            transport_config["port"] = self._config.get("email_port", "587")
            transport_config["encrypt_key"] = self._config.get("encrypt_key", "")

        return transport_config

    def get_config(self):
        # type: () -> Dict[str, Any]
        """
        Get the complete loaded configuration.

        Returns:
            Dict containing all configuration settings
        """
        return self._config.copy() if self._loaded else {}

    def get_config_value(self, key, default=None):
        # type: (str, Any) -> Any
        """
        Get a specific configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default) if self._loaded else default
