import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import (
    EMAIL_PROVIDER,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
    SENDER_EMAIL,
    RECIPIENT_EMAIL,
    RESEND_API_KEY,
    DIGEST_TITLE,
)

logger = logging.getLogger(__name__)


class EmailSender:
    """Dispatches HTML newsletters via free Gmail SMTP or Resend API."""

    def __init__(self):
        self.provider = EMAIL_PROVIDER
        self.recipient = RECIPIENT_EMAIL
        self.sender = SENDER_EMAIL

    def send_digest(self, subject: str, html_content: str, text_content: str = "") -> bool:
        """Sends the digest email using the configured provider."""
        if not self.recipient:
            raise ValueError(
                "RECIPIENT_EMAIL is not set in .env. Please configure where to send the morning digest."
            )

        if self.provider == "resend":
            return self._send_via_resend(subject, html_content)
        else:
            return self._send_via_smtp(subject, html_content, text_content)

    def _send_via_smtp(self, subject: str, html_content: str, text_content: str) -> bool:
        """Sends email via standard SMTP (e.g. Gmail App Password)."""
        if not SMTP_USER or not SMTP_PASS:
            raise ValueError(
                "SMTP credentials missing. Please set SMTP_USER and SMTP_PASS (Gmail App Password) in your .env file."
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{DIGEST_TITLE} | {subject}"
        msg["From"] = f"X Tech Radar <{self.sender}>"
        msg["To"] = self.recipient

        # Attach plain text and HTML versions
        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}...")
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(self.sender, [self.recipient], msg.as_string())
            logger.info(f"Email successfully delivered to {self.recipient} via SMTP!")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch email via SMTP: {e}")
            raise

    def _send_via_resend(self, subject: str, html_content: str) -> bool:
        """Sends email via Resend API."""
        if not RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY is missing in your .env file.")

        try:
            import resend
            resend.api_key = RESEND_API_KEY
            params = {
                "from": self.sender or "onboarding@resend.dev",
                "to": [self.recipient],
                "subject": f"{DIGEST_TITLE} | {subject}",
                "html": html_content,
            }
            resend.Emails.send(params)
            logger.info(f"Email successfully delivered to {self.recipient} via Resend!")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch email via Resend: {e}")
            raise
