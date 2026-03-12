"""
Delivery Agent -- Sends reports via Slack and Email.

Responsibilities:
- Send report summaries to Slack via webhook
- Send full reports via email using smtplib
- Track delivery status for each channel
- Handle delivery failures gracefully
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

import httpx

from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient


class DeliveryAgent(BaseAgent):
    """
    Agent that delivers generated reports via Slack and Email.

    Input:
        report_markdown: str -- The report content in Markdown
        report_title: str -- Report title
        report_metadata: dict -- Report generation metadata
        insights: dict -- Analysis insights for summary
        delivery_channels: list[str] -- Channels to deliver to: ["slack", "email"]
        email_recipients: list[str] (optional) -- Email addresses for email delivery
        pdf_path: str (optional) -- Path to PDF attachment

    Output:
        delivery_results: dict -- Status of each delivery channel
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="delivery_agent", db=db)
        self.settings = get_settings()

    async def run(self, input_data: dict) -> dict:
        report_markdown: str = input_data["report_markdown"]
        report_title: str = input_data["report_title"]
        insights: dict = input_data.get("insights", {})
        channels: list[str] = input_data.get("delivery_channels", [])
        email_recipients: list[str] = input_data.get("email_recipients", [])
        pdf_path: str | None = input_data.get("pdf_path")

        self.logger.info(f"Delivering report to channels: {channels}")
        delivery_results = {}

        # ── Slack delivery ──
        if "slack" in channels:
            delivery_results["slack"] = await self._send_slack(report_title, insights, report_markdown)

        # ── Email delivery ──
        if "email" in channels and email_recipients:
            delivery_results["email"] = await self._send_email(
                recipients=email_recipients,
                subject=report_title,
                body_markdown=report_markdown,
                pdf_path=pdf_path,
            )

        # ── Log channel ── (always delivers to database log)
        delivery_results["log"] = {"status": "delivered", "detail": "Report logged to database"}

        success_count = sum(1 for r in delivery_results.values() if r.get("status") == "delivered")
        total_count = len(delivery_results)

        self.logger.info(f"Delivery complete: {success_count}/{total_count} channels succeeded")

        return {"delivery_results": delivery_results}

    async def _send_slack(self, title: str, insights: dict, full_report: str) -> dict:
        """Send a report summary to Slack via incoming webhook."""
        webhook_url = self.settings.slack_webhook_url
        if not webhook_url:
            self.logger.warning("Slack webhook URL not configured -- skipping")
            return {"status": "skipped", "detail": "Webhook URL not configured"}

        try:
            # Build Slack message with Block Kit
            executive_summary = insights.get("executive_summary", "Report generated successfully.")
            findings = insights.get("key_findings", [])
            recommendations = insights.get("recommendations", [])

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"📊 {title}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Executive Summary*\n{executive_summary}"}
                },
                {"type": "divider"},
            ]

            # Key findings (top 3)
            if findings:
                finding_text = "*Key Findings:*\n"
                for f in findings[:3]:
                    impact = f.get("impact", "").upper()
                    icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(impact, "⚪")
                    finding_text += f"{icon} {f.get('finding', '')}\n"
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": finding_text}})

            # Top recommendations (top 2)
            if recommendations:
                rec_text = "*Top Recommendations:*\n"
                for r in recommendations[:2]:
                    rec_text += f"→ *{r.get('title', '')}*: {r.get('description', '')}\n"
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": rec_text}})

            payload = {"blocks": blocks}

            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()

            self.logger.info("Slack delivery: SUCCESS")
            return {"status": "delivered", "detail": "Message sent to Slack"}

        except Exception as e:
            self.logger.error(f"Slack delivery failed: {e}")
            return {"status": "failed", "detail": str(e)}

    async def _send_email(
        self,
        recipients: list[str],
        subject: str,
        body_markdown: str,
        pdf_path: str | None = None,
    ) -> dict:
        """Send report via email using SMTP (smtplib)."""
        smtp_host = self.settings.smtp_host
        smtp_port = self.settings.smtp_port
        smtp_user = self.settings.smtp_username
        smtp_pass = self.settings.smtp_password

        if not smtp_user or not smtp_pass:
            self.logger.warning("SMTP credentials not configured -- skipping email")
            return {"status": "skipped", "detail": "SMTP credentials not configured"}

        try:
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = ", ".join(recipients)

            # Convert markdown to simple HTML for email body
            html_body = self._markdown_to_html(body_markdown)

            # Attach HTML body
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

            # Attach PDF if available
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(pdf_path),
                    )
                    msg.attach(pdf_attachment)

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            self.logger.info(f"Email delivery: SUCCESS -> {recipients}")
            return {
                "status": "delivered",
                "detail": f"Email sent to {len(recipients)} recipients",
                "recipients": recipients,
            }

        except Exception as e:
            self.logger.error(f"Email delivery failed: {e}")
            return {"status": "failed", "detail": str(e)}

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to simple HTML for email rendering."""
        try:
            import markdown
            html = markdown.markdown(
                markdown_text,
                extensions=["tables", "fenced_code"],
            )
            return f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px;
                        margin: 0 auto; padding: 20px; color: #333; line-height: 1.6;">
                {html}
            </div>
            """
        except ImportError:
            # Fallback: wrap in <pre> if markdown library not available
            return f"<pre style='font-family: monospace; white-space: pre-wrap;'>{markdown_text}</pre>"
