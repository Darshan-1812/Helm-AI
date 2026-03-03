"""
Alert Worker — async notification delivery via Dramatiq.

Sends alerts to configured channels (webhook, Slack, email)
when guardrails fire or quality gates fail.
"""

import dramatiq
import json
import logging

from app.services.alert_service import dispatcher

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=2000, max_backoff=60000)
def send_alert_notification(alert_data_json: str, channels_json: str):
    """
    Send alert notifications to configured channels.

    Args:
        alert_data_json: JSON-encoded alert payload
        channels_json: JSON-encoded list of notification channel configs
            e.g., [
                {"type": "webhook", "url": "https://..."},
                {"type": "slack", "webhook_url": "https://hooks.slack.com/..."},
                {"type": "email", "to": "ops@example.com"},
            ]
    """
    alert_data = json.loads(alert_data_json)
    channels = json.loads(channels_json)

    logger.info(
        f"Dispatching alert to {len(channels)} channels: "
        f"type={alert_data.get('alert_type')}, severity={alert_data.get('severity')}"
    )

    results = {}
    for channel in channels:
        channel_type = channel.get("type", "")

        try:
            if channel_type == "webhook":
                ok = dispatcher.send_webhook(url=channel["url"], alert_data=alert_data)
                results[f"webhook:{channel['url'][:30]}"] = ok

            elif channel_type == "slack":
                ok = dispatcher.send_slack(webhook_url=channel["webhook_url"], alert_data=alert_data)
                results[f"slack"] = ok

            elif channel_type == "email":
                ok = dispatcher.send_email(to=channel["to"], alert_data=alert_data)
                results[f"email:{channel['to']}"] = ok

            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                results[channel_type] = False

        except Exception as e:
            logger.error(f"Channel {channel_type} failed: {e}")
            results[channel_type] = False

    success_count = sum(1 for v in results.values() if v)
    logger.info(f"Alert dispatch complete: {success_count}/{len(channels)} channels succeeded")

    return results


@dramatiq.actor(max_retries=2, min_backoff=1000, max_backoff=30000)
def send_quality_gate_alert(run_id: str, org_id: str, eval_type: str, score: float, threshold: float):
    """
    Send a quality gate failure alert.
    Called by the eval_worker when a score falls below threshold.
    """
    alert_data = {
        "alert_type": "quality_gate",
        "severity": "critical" if score < 0.3 else "warning",
        "run_id": run_id,
        "message": (
            f"Quality gate failed: {eval_type} score {score:.2f} "
            f"is below threshold {threshold:.2f}"
        ),
        "details": {
            "eval_type": eval_type,
            "score": score,
            "threshold": threshold,
        },
    }

    logger.warning(
        f"Quality gate alert: run={run_id}, {eval_type}={score:.2f} < {threshold:.2f}"
    )

    # TODO: Fetch notification channels from org config in DB
    # For now, just log it
    logger.info(f"Alert data: {json.dumps(alert_data, indent=2)}")
