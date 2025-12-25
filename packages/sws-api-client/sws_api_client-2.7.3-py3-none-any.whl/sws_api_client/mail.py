"""Mail Module for SWS API Client.

This module provides email functionality using SMTP with automatic fallback
to console logging when SMTP is not available.
"""

import os
import logging
import smtplib
from typing import Optional

logger = logging.getLogger(__name__)


class Mail:
    """Mail class for sending emails via SMTP.
    
    This class provides a simple interface for sending emails through an SMTP server.
    If SMTP configuration is not available or the server is unreachable, it falls back
    to logging the email content to the console.
    
    Environment Variables:
        SMTP_HOST: SMTP server hostname (optional)
        SMTP_PORT: SMTP server port (optional, defaults to 25)
    
    Example:
        >>> mail = Mail()
        >>> mail.send_mail(
        ...     sender_email="sender@example.com",
        ...     receiver_email="receiver@example.com",
        ...     message="Subject: Test\\n\\nThis is a test email"
        ... )
    """
    
    def __init__(self):
        """Initialize Mail client with SMTP configuration from environment variables."""
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.server: Optional[smtplib.SMTP] = None
        self._server_available = False
        
        # Try to establish SMTP connection
        if self.smtp_host:
            try:
                logger.info(f"Attempting to connect to SMTP server at {self.smtp_host}:{self.smtp_port}")
                self.server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                self._server_available = True
                logger.info(f"✅ Successfully connected to SMTP server at {self.smtp_host}:{self.smtp_port}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to SMTP server at {self.smtp_host}:{self.smtp_port}: {e}")
                logger.warning("📧 Will fallback to console logging for emails")
                self.server = None
                self._server_available = False
        else:
            logger.info("📧 SMTP_HOST not configured, emails will be logged to console")
    
    def send_mail(self, sender_email: str, receiver_email: str, message: str) -> bool:
        """Send an email via SMTP or log to console if SMTP is not available.
        
        Args:
            sender_email (str): Email address of the sender
            receiver_email (str): Email address of the receiver
            message (str): Complete email message including headers and body.
                          Should follow RFC 822 format (e.g., "Subject: Test\\n\\nBody text")
        
        Returns:
            bool: True if email was sent successfully via SMTP, False if logged to console
        
        Example:
            >>> mail = Mail()
            >>> mail.send_mail(
            ...     "from@example.com",
            ...     "to@example.com", 
            ...     "Subject: Hello\\n\\nThis is the email body"
            ... )
        """
        if self._server_available and self.server:
            try:
                self.server.sendmail(sender_email, receiver_email, message)
                logger.info(f"✅ Email sent successfully from {sender_email} to {receiver_email}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to send email via SMTP: {e}")
                logger.info("📧 Logging email to console instead:")
                self._log_email_to_console(sender_email, receiver_email, message)
                return False
        else:
            # Fallback to console logging
            self._log_email_to_console(sender_email, receiver_email, message)
            return False
    
    def _log_email_to_console(self, sender_email: str, receiver_email: str, message: str):
        """Log email details to console when SMTP is not available.
        
        Args:
            sender_email (str): Email address of the sender
            receiver_email (str): Email address of the receiver
            message (str): Complete email message
        """
        logger.info("=" * 80)
        logger.info("📧 EMAIL (Console Log - SMTP not available)")
        logger.info("=" * 80)
        logger.info(f"From: {sender_email}")
        logger.info(f"To: {receiver_email}")
        logger.info("-" * 80)
        logger.info(message)
        logger.info("=" * 80)
    
    def close(self):
        """Close the SMTP connection if it exists."""
        if self.server:
            try:
                self.server.quit()
                logger.info("SMTP connection closed")
            except Exception as e:
                logger.warning(f"Error closing SMTP connection: {e}")
            finally:
                self.server = None
                self._server_available = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures SMTP connection is closed."""
        self.close()
