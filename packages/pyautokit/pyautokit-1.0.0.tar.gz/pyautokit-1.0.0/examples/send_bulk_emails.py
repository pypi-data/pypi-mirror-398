#!/usr/bin/env python3
"""Example: Send bulk personalized emails."""

from pyautokit.email_automation import EmailClient
from pyautokit.logger import setup_logger

logger = setup_logger("BulkEmails")


def main():
    """Send bulk emails with templates."""
    # Sample recipient data
    recipients = [
        {"email": "user1@example.com", "name": "Alice", "project": "Website"},
        {"email": "user2@example.com", "name": "Bob", "project": "Mobile App"},
        {"email": "user3@example.com", "name": "Charlie", "project": "API"},
    ]
    
    # Email templates with variables
    subject_template = "Update on Your $project Project"
    body_template = """Hi $name,

I wanted to give you a quick update on the $project project.

Everything is progressing well and we're on track for the deadline.

Best regards,
The Team
"""
    
    client = EmailClient()
    
    logger.info(f"Sending {len(recipients)} emails")
    results = client.send_templated_emails(
        recipients,
        subject_template,
        body_template,
        html=False
    )
    
    logger.info(f"Success: {results['success']}, Failed: {results['failed']}")


if __name__ == "__main__":
    # NOTE: Configure EMAIL_* variables in .env before running
    main()
