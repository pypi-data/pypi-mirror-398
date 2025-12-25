#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line interface module for Metaport Python Agent.

This module handles argument parsing and validation, ensuring compatibility
with the command-line interface of the PHP and Node.js Metaport agents.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import argparse
import sys
import re


def parse_arguments(args=None):
    # type: (Optional[list]) -> argparse.Namespace
    """
    Parse command-line arguments for the Metaport agent.

    Implements the same argument structure as the PHP and Node.js agents
    to ensure consistency across all Metaport agent implementations.

    Args:
        args: Optional list of arguments to parse. If None, uses sys.argv.

    Returns:
        argparse.Namespace: Parsed arguments object containing all CLI parameters.
    """
    parser = argparse.ArgumentParser(
        description="Metaport Python Agent - Generate and transmit SBOM documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --transport=http --name=myapp --host=metaport.dev \\
           --uuid=12345678-1234-1234-1234-123456789012 \\
           --domain=example.com --env=PROD --version=1.0.0 \\
           --auth='your-auth-token'

  %(prog)s --transport=email --name=myapp --host=smtp.example.com \\
           --uuid=12345678-1234-1234-1234-123456789012 \\
           --domain=example.com --env=PROD --version=2.1.0 \\
           --auth='<metaport email public key>' --classic=1

Environment Variables:
  MAILER_DSN                The connection DSN to parse+inject into config
  MP_MAIL_TRANSPORT_PUBKEY  Encryption key for email attachments
  MP_IGNORE_CERT            Ignore SSL certificate validation (0|1)
  MP_RETAIN_SBOM            Retain SBOM files locally after transmission (0|1)
        """,
    )

    # Required arguments
    parser.add_argument(
        "--transport",
        required=True,
        choices=["http", "email"],
        help="Transport method for sending SBOM data (http|email)",
    )

    parser.add_argument("--name", required=True, help="Application name identifier")

    parser.add_argument(
        "--host", required=True, help="Metaport instance hostname or mailbox address"
    )

    parser.add_argument(
        "--uuid",
        required=True,
        help="Unique identifier for the application",
    )

    parser.add_argument(
        "--domain", required=True, help="Domain associated with the application"
    )

    parser.add_argument(
        "--env", required=True, help="Environment identifier (e.g., PROD, STAGING, DEV)"
    )

    parser.add_argument("--version", required=True, help="Application version string")

    parser.add_argument(
        "--auth", required=True, help="Authentication token or credentials"
    )

    # Optional arguments
    parser.add_argument(
        "--classic",
        choices=["0", "1"],
        default="0",
        help="Classic mode flag (0|1, default: 0)",
    )

    # Parse arguments
    if args is None:
        parsed_args = parser.parse_args()
    else:
        parsed_args = parser.parse_args(args)

    return parsed_args


def validate_arguments(args):
    # type: (argparse.Namespace) -> bool
    """
    Validate parsed command-line arguments.

    Performs additional validation beyond basic argument parsing to ensure
    all required parameters are properly formatted and consistent with
    Metaport agent requirements.

    Args:
        args: Parsed arguments from parse_arguments()

    Returns:
        bool: True if all arguments are valid, False otherwise.

    Note:
        This function will print error messages to stderr and return False
        for invalid arguments. The calling code should exit with a non-zero
        exit code when validation fails.
    """
    errors = []

    # Validate transport method
    if args.transport not in ["http", "email"]:
        errors.append("Transport must be 'http' or 'email'")

    # Validate UUID format (basic check)
    uuid_str = args.uuid
    if len(uuid_str) != 36 or uuid_str.count("-") != 4:
        errors.append(
            "UUID must be in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
        )

    # Validate name (non-empty, reasonable length)
    if not args.name or len(args.name.strip()) == 0:
        errors.append("Application name cannot be empty")
    elif len(args.name) > 255:
        errors.append("Application name too long (max 255 characters)")

    # Validate host (non-empty)
    if not args.host or len(args.host.strip()) == 0:
        errors.append("Host cannot be empty")

    # Validate domain (non-empty)
    if not args.domain or len(args.domain.strip()) == 0:
        errors.append("Domain cannot be empty")

    if re.match(r'^http', args.domain):
        errors.append("Domain argument should not contain scheme")

    if re.match(r'[^\w\d\.\-]', args.domain) or '.' not in args.domain:
        errors.append("Domain argument should be a valid domain")

    # Validate environment (non-empty)
    if not args.env or len(args.env.strip()) == 0:
        errors.append("Environment cannot be empty")

    # Validate version (non-empty)
    if not args.version or len(args.version.strip()) == 0:
        errors.append("Version cannot be empty")

    # Validate auth (non-empty)
    if not args.auth or len(args.auth.strip()) == 0:
        errors.append("Authentication token cannot be empty")

    # Validate classic flag
    if args.classic not in ["0", "1"]:
        errors.append("Classic flag must be '0' or '1'")

    # Validate host:
    # - Should be an email address when --transport=email
    # - Should be not be an email address when --transport=http
    if args.transport == 'email' and not re.match(r'.+@.+\.', args.host):
        errors.append("Use a valid email address when passing --transport=email")

    if args.transport == 'http' and re.match(r'.+@', args.host):
        errors.append("Use a valid hostname or IP when passing --transport=http")

    # Print errors if any
    if errors:
        print("Error: Invalid command-line arguments:", file=sys.stderr)
        for error in errors:
            print("  - " + error, file=sys.stderr)
        return False

    return True


def print_version():
    # type: () -> None
    """Print version information for the Metaport Python agent."""
    try:
        from . import __version__

        print("Metaport Python Agent v{}".format(__version__))
    except ImportError:
        print("Metaport Python Agent v1.0.0")


def print_usage_examples():
    # type: () -> None
    """Print usage examples for the Metaport Python agent."""
    examples = [
        "# HTTPS transport example:",
        "./metaport/metaport.py \\",
        "    --transport=http \\",
        "    --name=my-python-app \\",
        "    --host=metaport.example.com \\",
        "    --uuid=12345678-1234-1234-1234-123456789012 \\",
        "    --domain=example.com \\",
        "    --env=PROD \\",
        "    --version=1.0.0 \\",
        "    --auth='your-auth-token'",
        "",
        "# Email transport example:",
        "./metaport/metaport.py \\",
        "    --transport=email \\",
        "    --name=my-python-app \\",
        "    --host=mailbox@example.com \\",
        "    --uuid=12345678-1234-1234-1234-123456789012 \\",
        "    --domain=example.com \\",
        "    --env=STAGING \\",
        "    --version=2.1.0 \\",
        "    --auth='email-credentials' \\",
        "    --classic=1",
    ]

    for line in examples:
        print(line)


if __name__ == "__main__":
    # Allow running this module directly for testing
    args = parse_arguments()
    if validate_arguments(args):
        print("Arguments are valid:")
        for key, value in vars(args).items():
            print("  {}: {}".format(key, value))
    else:
        sys.exit(1)
