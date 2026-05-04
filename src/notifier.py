import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def notify(violations: list) -> None:
    """Send Teams alert with violation summary via webhook."""
    
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        logger.error("TEAMS_WEBHOOK_URL not set in environment")
        exit(1)
    
    # Build the message
    lines = [f"⚠️ Cloud Guardian Alert — {len(violations)} violation(s) found\n"]
    for v in violations:
        missing = ", ".join(v["missing_tags"])
        lines.append(f"• {v['resource_name']} ({v['resource_type']}): missing {missing}")
    
    payload = {"text": "\n".join(lines)}
    
    # Send the alert
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info("Teams alert sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Teams alert: {e}")
        exit(1)