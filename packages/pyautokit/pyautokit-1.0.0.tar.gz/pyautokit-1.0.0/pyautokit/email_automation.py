"""Email automation with template support.

Features:
- SMTP support for Gmail and custom servers
- Template-based personalization
- Bulk email sending
- Attachment support
- HTML and plain text emails
"""

import argparse
import sys
import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict
from string import Template
from .logger import setup_logger
from .config import Config
from .utils import load_json

logger = setup_logger("EmailAutomation", level=Config.LOG_LEVEL)


class EmailClient:
    """Email automation client with SMTP."""

    def __init__(
        self,
        smtp_server: str = Config.EMAIL_SMTP_SERVER,
        smtp_port: int = Config.EMAIL_SMTP_PORT,
        sender: str = Config.EMAIL_SENDER,
        password: str = Config.EMAIL_PASSWORD,
        use_tls: bool = Config.EMAIL_USE_TLS
    ):
        """Initialize email client.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            sender: Sender email address
            password: Email password or app password
            use_tls: Use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.use_tls = use_tls

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[Path]] = None
    ) -> MIMEMultipart:
        """Create email message.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            html: Body is HTML
            attachments: List of file paths to attach
            
        Returns:
            MIMEMultipart message object
        """
        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html" if html else "plain"))

        if attachments:
            for file_path in attachments:
                if not file_path.exists():
                    logger.warning(f"Attachment not found: {file_path}")
                    continue
                
                with open(file_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={file_path.name}"
                )
                msg.attach(part)
        
        return msg

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """Send single email.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            html: Body is HTML
            attachments: List of attachments
            
        Returns:
            True if sent successfully
        """
        try:
            msg = self._create_message(to, subject, body, html, attachments)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    def send_bulk_emails(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict[str, int]:
        """Send bulk emails.
        
        Args:
            recipients: List of recipient emails
            subject: Email subject
            body: Email body
            html: Body is HTML
            
        Returns:
            Dict with success/failure counts
        """
        results = {"success": 0, "failed": 0}
        
        for recipient in recipients:
            if self.send_email(recipient, subject, body, html):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Bulk email complete: {results}")
        return results

    def send_templated_emails(
        self,
        recipients_data: List[Dict[str, str]],
        subject_template: str,
        body_template: str,
        html: bool = False
    ) -> Dict[str, int]:
        """Send templated emails with personalization.
        
        Args:
            recipients_data: List of dicts with 'email' and template variables
            subject_template: Subject template with $variable placeholders
            body_template: Body template with $variable placeholders
            html: Body is HTML
            
        Returns:
            Dict with success/failure counts
        """
        results = {"success": 0, "failed": 0}
        
        subject_tmpl = Template(subject_template)
        body_tmpl = Template(body_template)
        
        for data in recipients_data:
            email = data.get("email")
            if not email:
                logger.warning("Recipient data missing email field")
                results["failed"] += 1
                continue
            
            try:
                subject = subject_tmpl.safe_substitute(data)
                body = body_tmpl.safe_substitute(data)
                
                if self.send_email(email, subject, body, html):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Template error for {email}: {e}")
                results["failed"] += 1
        
        return results


def main() -> int:
    """CLI for email automation."""
    parser = argparse.ArgumentParser(
        description="Email automation with SMTP and templates",
        epilog="Examples:\n"
               "  %(prog)s --to user@example.com --subject 'Hello' --body 'Test'\n"
               "  %(prog)s --to user@example.com --subject 'Report' --body-file report.txt\n"
               "  %(prog)s --bulk recipients.csv --subject 'Update' --template email.txt\n"
               "  %(prog)s --templated data.json --subject-template 'Hi $name' --body-template body.txt\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Recipient options
    recipient_group = parser.add_mutually_exclusive_group(required=True)
    recipient_group.add_argument(
        "--to",
        help="Single recipient email"
    )
    recipient_group.add_argument(
        "--bulk",
        help="CSV file with emails (one per line or 'email' column)"
    )
    recipient_group.add_argument(
        "--templated",
        help="JSON file with recipient data for templated emails"
    )
    
    # Subject options
    parser.add_argument(
        "--subject",
        help="Email subject"
    )
    parser.add_argument(
        "--subject-template",
        help="Subject template for templated emails (use $variable)"
    )
    
    # Body options
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument(
        "--body",
        help="Email body text"
    )
    body_group.add_argument(
        "--body-file",
        help="File containing email body"
    )
    body_group.add_argument(
        "--template",
        help="Template file for bulk/templated emails"
    )
    
    # Additional options
    parser.add_argument(
        "--html",
        action="store_true",
        help="Send as HTML email"
    )
    
    parser.add_argument(
        "--attach",
        action="append",
        help="Attachment file path (can specify multiple)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without sending"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # Validate configuration
    if not Config.EMAIL_SENDER or not Config.EMAIL_PASSWORD:
        logger.error("Email configuration missing! Set EMAIL_SENDER and EMAIL_PASSWORD in .env")
        return 1
    
    client = EmailClient()
    
    # Load body
    if args.body:
        body = args.body
    elif args.body_file:
        body = Path(args.body_file).read_text()
    elif args.template:
        body = Path(args.template).read_text()
    else:
        body = ""
    
    # Handle attachments
    attachments = [Path(a) for a in args.attach] if args.attach else None
    
    # Single email
    if args.to:
        if args.dry_run:
            print(f"Would send to: {args.to}")
            print(f"Subject: {args.subject}")
            print(f"Body: {body[:100]}...")
            return 0
        
        success = client.send_email(
            to=args.to,
            subject=args.subject or "No Subject",
            body=body,
            html=args.html,
            attachments=attachments
        )
        return 0 if success else 1
    
    # Bulk emails
    elif args.bulk:
        # Load recipients from CSV
        recipients = []
        with open(args.bulk, 'r') as f:
            reader = csv.DictReader(f)
            if 'email' in reader.fieldnames:
                recipients = [row['email'] for row in reader]
            else:
                # Assume one email per line
                f.seek(0)
                recipients = [line.strip() for line in f if line.strip()]
        
        if args.dry_run:
            print(f"Would send to {len(recipients)} recipients")
            print(f"Subject: {args.subject}")
            return 0
        
        results = client.send_bulk_emails(
            recipients,
            args.subject or "No Subject",
            body,
            args.html
        )
        print(f"✅ Sent: {results['success']}, ❌ Failed: {results['failed']}")
        return 0 if results['failed'] == 0 else 1
    
    # Templated emails
    elif args.templated:
        recipients_data = load_json(Path(args.templated))
        
        if args.dry_run:
            print(f"Would send templated emails to {len(recipients_data)} recipients")
            return 0
        
        results = client.send_templated_emails(
            recipients_data,
            args.subject_template or args.subject or "No Subject",
            body,
            args.html
        )
        print(f"✅ Sent: {results['success']}, ❌ Failed: {results['failed']}")
        return 0 if results['failed'] == 0 else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
