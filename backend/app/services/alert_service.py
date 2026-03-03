"""
Alert Service — webhook and notification dispatch.

Supports:
- Webhook (POST to any URL)
- Slack (via incoming webhook)
- Email (logged stub, ready for SMTP/SendGrid)
"""

import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """
    Dispatches alert notifications to configured channels.

    Usage:
        dispatcher = AlertDispatcher()
        dispatcher.send_webhook(url="https://...", alert_data={...})
        dispatcher.send_slack(webhook_url="https://hooks.slack.com/...", alert_data={...})
    """

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    # ── Webhook ──────────────────────────────────────
    def send_webhook(self, url: str, alert_data: dict) -> bool:
        """
        Send alert data to a webhook URL via HTTP POST.

        Args:
            url: Target webhook URL
            alert_data: Alert payload
        Returns:
            True if successful, False otherwise
        """
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    url,
                    json={
                        "event": "guardrail_alert",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data": alert_data,
                    },
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code < 300:
                    logger.info(f"Webhook sent to {url}: {response.status_code}")
                    return True
                else:
                    logger.warning(f"Webhook failed: {url} → {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Webhook error for {url}: {e}")
            return False

    # ── Slack ────────────────────────────────────────
    def send_slack(self, webhook_url: str, alert_data: dict) -> bool:
        """
        Send alert notification to Slack via incoming webhook.

        Args:
            webhook_url: Slack incoming webhook URL
            alert_data: Alert payload
        Returns:
            True if successful, False otherwise
        """
        severity = alert_data.get("severity", "warning")
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "⚠️")
        severity_color = {"info": "#36a64f", "warning": "#ff9800", "critical": "#f44336"}.get(severity, "#ff9800")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} Agent Control Room Alert",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:*\n{alert_data.get('alert_type', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Agent:*\n{alert_data.get('agent_name', '—')}"},
                    {"type": "mrkdwn", "text": f"*Run ID:*\n`{alert_data.get('run_id', '—')}`"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{alert_data.get('message', 'No message')}",
                },
            },
        ]

        payload = {
            "blocks": blocks,
            "attachments": [{"color": severity_color, "text": ""}],
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    logger.info(f"Slack alert sent: {alert_data.get('alert_type')}")
                    return True
                else:
                    logger.warning(f"Slack failed: {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Slack error: {e}")
            return False

    # ── Email (Stub) ─────────────────────────────────
    def send_email(
        self,
        to: str,
        alert_data: dict,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
    ) -> bool:
        """
        Send alert notification via email.
        Currently logs the email — implement SMTP or SendGrid for production.

        Args:
            to: Recipient email
            alert_data: Alert payload
        Returns:
            True if logged successfully
        """
        severity = alert_data.get("severity", "warning")
        subject = f"[ACR {severity.upper()}] {alert_data.get('alert_type', 'Alert')}"
        body = (
            f"Agent Control Room Alert\n"
            f"{'=' * 40}\n"
            f"Type: {alert_data.get('alert_type', 'unknown')}\n"
            f"Severity: {severity}\n"
            f"Agent: {alert_data.get('agent_name', '—')}\n"
            f"Run ID: {alert_data.get('run_id', '—')}\n"
            f"Message: {alert_data.get('message', 'No message')}\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n"
        )

        logger.info(f"Email alert (stub):\n  To: {to}\n  Subject: {subject}\n{body}")

        # TODO: Implement with smtplib or SendGrid
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(body)
        # msg['Subject'] = subject
        # msg['To'] = to
        # ...

        return True


# Singleton instance
dispatcher = AlertDispatcher()
