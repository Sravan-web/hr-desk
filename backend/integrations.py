"""
Strategy #3: Third-Party API Integrations — The "WOW" Factor
=============================================================
Chaining existing APIs together to create high-impact features
without building anything from scratch.

Integrations:
- Twilio: SMS notifications when tickets are escalated
- SendGrid: Email confirmations for ticket status updates
- Slack Webhook: Real-time alerts to the HR team channel

All integrations are optional — if API keys aren't set,
they degrade gracefully with console logs instead.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger("hrbot.integrations")


# ═══════════════════════════════════════════════════════════════════════
# 1. TWILIO — SMS Notifications for Escalated Tickets
# ═══════════════════════════════════════════════════════════════════════

class TwilioNotifier:
    """
    Sends SMS alerts to HR when a HIGH priority ticket is created.
    Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
              HR_PHONE_NUMBER in .env
    """

    def __init__(self):
        self.enabled = False
        self.client = None

        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.hr_number = os.getenv("HR_PHONE_NUMBER")

        if sid and token and self.from_number and self.hr_number:
            try:
                from twilio.rest import Client
                self.client = Client(sid, token)
                self.enabled = True
                logger.info("✅ Twilio SMS integration active")
            except ImportError:
                logger.info("ℹ️  Twilio package not installed — SMS disabled")
        else:
            logger.info("ℹ️  Twilio not configured — SMS notifications disabled")

    def send_escalation_alert(self, ticket_id: str, employee_id: str,
                               query: str, priority: str) -> bool:
        """Send an SMS to HR about a new escalated ticket."""
        message_body = (
            f"🚨 HRBot Escalation Alert\n"
            f"Ticket: {ticket_id}\n"
            f"Priority: {priority}\n"
            f"Employee: {employee_id}\n"
            f"Query: {query[:100]}..."
        )

        if self.enabled and self.client:
            try:
                msg = self.client.messages.create(
                    body=message_body,
                    from_=self.from_number,
                    to=self.hr_number,
                )
                logger.info(f"SMS sent: {msg.sid}")
                return True
            except Exception as e:
                logger.error(f"SMS failed: {e}")
                return False
        else:
            # Graceful fallback — log instead of crash
            logger.info(f"[SMS MOCK] Would send: {message_body}")
            return False


# ═══════════════════════════════════════════════════════════════════════
# 2. SLACK WEBHOOK — Real-Time HR Channel Alerts
# ═══════════════════════════════════════════════════════════════════════

class SlackNotifier:
    """
    Posts ticket alerts to a Slack channel via incoming webhook.
    Requires: SLACK_WEBHOOK_URL in .env
    """

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

        if self.enabled:
            logger.info("✅ Slack webhook integration active")
        else:
            logger.info("ℹ️  Slack webhook not configured")

    async def send_ticket_alert(self, ticket_id: str, employee_id: str,
                                 query: str, priority: str) -> bool:
        """Post a rich message to the HR Slack channel."""
        color = "#dc2626" if priority == "HIGH" else "#f59e0b"
        emoji = "🔴" if priority == "HIGH" else "🟡"

        payload = {
            "attachments": [{
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} New Escalation: {ticket_id}",
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                            {"type": "mrkdwn", "text": f"*Employee:*\n{employee_id}"},
                            {"type": "mrkdwn", "text": f"*Query:*\n{query[:200]}"},
                            {"type": "mrkdwn", "text": f"*Status:*\nOPEN — Awaiting Review"},
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Open Dashboard"},
                            "url": os.getenv("DASHBOARD_URL", "http://localhost:5173"),
                            "style": "primary",
                        }]
                    }
                ]
            }]
        }

        if self.enabled:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        self.webhook_url,
                        json=payload,
                        timeout=5.0,
                    )
                    logger.info(f"Slack alert sent: {resp.status_code}")
                    return resp.status_code == 200
            except Exception as e:
                logger.error(f"Slack alert failed: {e}")
                return False
        else:
            logger.info(f"[SLACK MOCK] Would post: {ticket_id} ({priority})")
            return False


# ═══════════════════════════════════════════════════════════════════════
# 3. EMAIL — SendGrid Ticket Confirmations
# ═══════════════════════════════════════════════════════════════════════

class EmailNotifier:
    """
    Sends email confirmations when tickets are created or resolved.
    Requires: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL in .env
    """

    def __init__(self):
        self.enabled = False
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "hrbot@company.com")

        if self.api_key:
            try:
                import sendgrid
                self.enabled = True
                logger.info("✅ SendGrid email integration active")
            except ImportError:
                logger.info("ℹ️  SendGrid package not installed — email disabled")
        else:
            logger.info("ℹ️  SendGrid not configured — email notifications disabled")

    def send_ticket_confirmation(self, to_email: str, ticket_id: str,
                                  query: str) -> bool:
        """Send a ticket confirmation email to the employee."""
        if self.enabled:
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail

                message = Mail(
                    from_email=self.from_email,
                    to_emails=to_email,
                    subject=f"[HRBot] Ticket Created: {ticket_id}",
                    html_content=(
                        f"<h2>Your HR ticket has been created</h2>"
                        f"<p><strong>Reference:</strong> {ticket_id}</p>"
                        f"<p><strong>Your query:</strong> {query}</p>"
                        f"<p>Our HR team will review this within 24 business hours.</p>"
                        f"<p>— HRBot</p>"
                    ),
                )
                sg = sendgrid.SendGridAPIClient(self.api_key)
                response = sg.send(message)
                logger.info(f"Email sent: {response.status_code}")
                return True
            except Exception as e:
                logger.error(f"Email failed: {e}")
                return False
        else:
            logger.info(f"[EMAIL MOCK] Would send ticket confirmation to {to_email}")
            return False


# ═══════════════════════════════════════════════════════════════════════
# Unified Notification Dispatcher
# ═══════════════════════════════════════════════════════════════════════

class NotificationHub:
    """
    Central dispatcher that fans out notifications to all configured channels.
    If none are configured, everything degrades gracefully to console logs.
    """

    def __init__(self):
        self.twilio = TwilioNotifier()
        self.slack = SlackNotifier()
        self.email = EmailNotifier()

    async def notify_escalation(self, ticket_id: str, employee_id: str,
                                 query: str, priority: str,
                                 employee_email: Optional[str] = None):
        """Fan out escalation notifications to all active channels."""
        results = {"sms": False, "slack": False, "email": False}

        # SMS — synchronous (Twilio SDK is sync)
        if priority == "HIGH":
            results["sms"] = self.twilio.send_escalation_alert(
                ticket_id, employee_id, query, priority
            )

        # Slack — async
        results["slack"] = await self.slack.send_ticket_alert(
            ticket_id, employee_id, query, priority
        )

        # Email — synchronous
        if employee_email:
            results["email"] = self.email.send_ticket_confirmation(
                employee_email, ticket_id, query
            )

        active = [k for k, v in results.items() if v]
        logger.info(
            f"NOTIFICATION | ticket={ticket_id} | "
            f"channels_notified={active or 'none (demo mode)'}"
        )
        return results

    @property
    def status(self) -> dict:
        """Integration status for the admin dashboard."""
        return {
            "sms_twilio": self.twilio.enabled,
            "slack_webhook": self.slack.enabled,
            "email_sendgrid": self.email.enabled,
        }


# Singleton
notifications = NotificationHub()
