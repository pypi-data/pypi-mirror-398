#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of Metaport Python Agent

(c) Dcentrica <hello@dcentrica.com>

:package: metaport-agent-python
:author: Dcentrica 2025 <hello@dcentrica.com>

For the full copyright and license information, please view the LICENSE.txt
file that was distributed with this source code.

Email transport module for Metaport Python Agent.

This module handles transmission of SBOM documents and metadata via email
with encrypted attachments, supporting SMTP with STARTTLS authentication
and proper email formatting.

Supports Python 3.10+ with appropriate type hints and error handling.
"""

import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailTransport(object):
    """
    Email transport for sending SBOM data via encrypted email attachments.

    Handles transmission of SBOM documents as encrypted attachments to
    unencrypted email messages, supporting SMTP with STARTTLS and proper
    authentication.

    Features:
        - SMTP with STARTTLS support
        - Authentication with username/password
        - Encrypted attachment support (via EncryptionManager)
        - Proper MIME message formatting
        - Error handling and exit codes
    """

    def __init__(self, config=None):
        # type: (Optional[Dict[str, Any]]) -> None
        """
        Initialize email transport with configuration.

        Args:
            config: Transport configuration dict containing SMTP settings
        """
        self._config = config or {}
        self._smtp_connection = None  # type: Optional[smtplib.SMTP]

    def send(self, sbom, metadata):
        # type: (Dict[str, Any], Dict[str, str]) -> bool
        """
        Send SBOM document and metadata via email with encrypted attachment.

        Creates an email message with the SBOM document as an encrypted
        attachment and sends it via SMTP to the configured recipient.

        Args:
            sbom: SBOM document dict to transmit
            metadata: Application metadata dict

        Returns:
            True if transmission successful, False otherwise
        """
        # Validate configuration
        valid_config = self._validate_config()

        if not valid_config:
            returnStruct = {
                "success": False,
                "code": 400,
                "message": "Invalid SMTP configuration",
            }

            print(json.dumps(returnStruct), file=sys.stderr)

            return False

        # Prepare SBOM data for encryption
        sbom_json = json.dumps(sbom, indent=2)
        sbom_data = sbom_json.encode("utf-8")

        # Encrypt the SBOM data (will be handled by EncryptionManager)
        encrypted_data = self._encrypt_sbom_data(sbom_data)
        if encrypted_data is None:
            returnStruct = {
                "success": False,
                "code": 400,
                "message": "Encryption failure",
            }

            print(json.dumps(returnStruct), file=sys.stderr)

            return False

        # Create email message
        message = self.create_email_message(encrypted_data, metadata)
        if not message:
            returnStruct = {
                "success": False,
                "code": 400,
                "message": "Unable to construct email message",
            }

            print(json.dumps(returnStruct), file=sys.stderr)

            return False

        # Send email
        try:
            smtp = self.connect_smtp()
            if not smtp:
                returnStruct = {
                    "success": False,
                    "code": 400,
                    "message": "SMTP connection error",
                }

                print(json.dumps(returnStruct), file=sys.stderr)

                return False

            # Send the message
            from_addr = self._config.get("user", "")
            to_addr = self._get_recipient_address(metadata)

            smtp.send_message(message, from_addr, [to_addr])
            smtp.quit()

            returnStruct = {
                "success": True,
                "code": 202,
                "message": "OK",
            }

            print(json.dumps(returnStruct), file=sys.stderr)

            return True

        except smtplib.SMTPAuthenticationError:
            msg = "SMTP authentication failed"
        except smtplib.SMTPConnectError:
            msg = "SMTP connection failed"
        except smtplib.SMTPException:
            msg = "SMTP error"
        except Exception:
            msg = "Unexpected error during email transmission"
        finally:
            if self._smtp_connection:
                try:
                    self._smtp_connection.quit()
                except Exception:
                    pass
                self._smtp_connection = None

        returnStruct = {
            "success": False,
            "code": 400,
            "message": msg,
        }

        print(json.dumps(returnStruct), file=sys.stderr)

        return False

    def create_email_message(self, sbom_data, metadata):
        # type: (bytes, Dict[str, str]) -> Optional[MIMEMultipart]
        """
        Create email message with encrypted SBOM attachment.

        Creates a properly formatted MIME email message containing the
        encrypted SBOM data as an attachment to an unencrypted email.

        Args:
            sbom_data: Encrypted SBOM data as bytes
            metadata: Application metadata for email content

        Returns:
            MIMEMultipart message object or None if creation fails
        """
        try:
            # Create multipart message
            message = MIMEMultipart()

            # Set email headers
            from_addr = self._config.get("user", "")
            to_addr = self._get_recipient_address(metadata)

            message["From"] = from_addr
            message["To"] = to_addr
            message["Subject"] = metadata.get("uuid", metadata.get("name", ""))

            message.attach(MIMEText("", "plain"))

            # Create encrypted attachment
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(sbom_data)
            encoders.encode_base64(attachment)

            # Set attachment headers
            attachment.add_header(
                "Content-Disposition", 'attachment; filename="metaport-bom.json.enc"'
            )

            message.attach(attachment)

            return message

        except Exception:
            return None

    def connect_smtp(self):
        # type: () -> Optional[smtplib.SMTP]
        """
        Establish SMTP connection with STARTTLS authentication.

        Creates and configures SMTP connection with proper authentication
        and STARTTLS encryption for secure email transmission.

        Returns:
            SMTP connection object or None if connection fails
        """
        try:
            host = self._config.get("host", "")
            port = self._config.get("port", 587)  # Default SMTP submission port

            # Create SMTP connection
            smtp = smtplib.SMTP(host, port)

            # Enable debug output if needed (disabled for production)
            # smtp.set_debuglevel(1)

            # Start TLS encryption
            smtp.starttls()

            # Authenticate
            user = self._config.get("user", "")
            password = self._config.get("pass", "")

            if user and password:
                smtp.login(user, password)

            self._smtp_connection = smtp
            return smtp

        except smtplib.SMTPException:
            return None
        except Exception:
            return None

    def _validate_config(self):
        # type: () -> bool
        """
        Validate email transport configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self._config.get("host"):
            print(
                "Error: No SMTP host configured - check MAILER_DSN environment variable",
                file=sys.stderr,
            )
            return False

        if not self._config.get("user"):
            print(
                "Error: No SMTP username configured - check MAILER_DSN environment variable",
                file=sys.stderr,
            )
            return False

        if not self._config.get("pass"):
            print(
                "Error: No SMTP password configured - check MAILER_DSN environment variable",
                file=sys.stderr,
            )
            return False

        if not self._config.get("encrypt_key"):
            print(
                "Error: No encryption key configured for email transport",
                file=sys.stderr,
            )
            return False

        return True

    def _encrypt_sbom_data(self, sbom_data):
        # type: (bytes) -> Optional[bytes]
        """
        Encrypt SBOM data for email attachment.

        Uses the EncryptionManager to encrypt the SBOM data with the
        configured encryption key.

        Args:
            sbom_data: Raw SBOM data as bytes

        Returns:
            Encrypted data as bytes or None if encryption fails
        """
        try:
            # Import EncryptionManager here to avoid circular imports
            try:
                from .encryption_manager import EncryptionManager
            except ImportError:
                from encryption_manager import EncryptionManager

            encrypt_key = self._config.get("encrypt_key", "")
            if not encrypt_key:
                print("Error: No encryption key available", file=sys.stderr)
                return None

            encryption_manager = EncryptionManager()
            encrypted_data = encryption_manager.encrypt_attachment(
                sbom_data, encrypt_key
            )

            return encrypted_data

        except Exception as e:
            print(
                "Error: Could not encrypt SBOM data: {}".format(str(e)), file=sys.stderr
            )
            return None

    def _get_recipient_address(self, metadata):
        # type: (Dict[str, str]) -> str
        """
        Get recipient email address for SBOM transmission.

        When using email transport, the --host CLI argument serves as the recipient address.

        Args:
            metadata: Application metadata containing host from CLI

        Returns:
            Recipient email address
        """
        # For email transport, the --host argument is the recipient address
        recipient = metadata.get("host", "")
        if recipient:
            return recipient

        # Fallback: create recipient from domain (should not normally be needed)
        domain = metadata.get("domain", "example.com")
        return "metaport@{}".format(domain)

    def _create_attachment_filename(self, metadata):
        # type: (Dict[str, str]) -> str
        """
        Create filename for encrypted SBOM attachment.

        Args:
            metadata: Application metadata

        Returns:
            Attachment filename
        """
        app_name = metadata.get("name", "unknown")
        timestamp = self._get_current_timestamp().replace(":", "-").replace(" ", "_")

        return "sbom_{}_{}.enc".format(app_name, timestamp)

    def _get_current_timestamp(self):
        # type: () -> str
        """
        Get current timestamp for email content.

        Returns:
            Formatted timestamp string
        """
        from datetime import datetime

        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    def cleanup(self):
        # type: () -> None
        """
        Clean up email transport resources.

        Closes SMTP connection and performs any necessary cleanup.
        """
        if self._smtp_connection:
            try:
                self._smtp_connection.quit()
            except Exception:
                pass
            self._smtp_connection = None
