"""
Email sending functionality
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Optional
import pandas as pd

from .config import get_sender_config, get_receivers
from .html_generator import generate_html


def send(
    data: Any,
    subject: str = "Data Report",
    receivers: Optional[list] = None,
    title: Optional[str] = None
) -> None:
    """
    Send data as HTML email.
    
    Args:
        data: Data to send (dict, list, or pandas DataFrame)
        subject: Email subject
        receivers: List of receiver emails (optional, uses config if not provided)
        title: Title for the HTML page (optional, uses subject if not provided)
    
    Raises:
        Exception: If email sending fails
    """
    # Get configuration
    sender_config = get_sender_config()
    if receivers is None:
        receivers = get_receivers()
    
    if not receivers:
        raise ValueError("No receivers specified. Please configure receivers in config file or pass receivers parameter.")
    
    if title is None:
        title = subject
    
    # Generate HTML
    html_content = generate_html(data, title=title)
    
    # Create email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_config.get("address")
    msg["To"] = ", ".join(receivers)
    
    # Attach HTML content
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)
    
    # Send email
    try:
        smtp_server = sender_config.get("smtp_server", "smtp.gmail.com")
        smtp_port = sender_config.get("smtp_port", 587)
        sender_address = sender_config.get("address")
        sender_password = sender_config.get("password")
        
        if not sender_address or not sender_password:
            raise ValueError(
                "Sender email or password not configured. "
                "Please edit the config file with your email settings."
            )
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_address, sender_password)
            server.send_message(msg)
            # server.sendmail(sender_email, email, msg.as_string())
            server.quit()
        
        print(f"Email sent successfully to: {', '.join(receivers)}")


    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")

