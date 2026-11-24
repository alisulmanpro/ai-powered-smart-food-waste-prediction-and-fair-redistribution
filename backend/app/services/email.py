"""Transactional email delivery through the Brevo (formerly Sendinblue) SMTP API.

Uses plain HTTP via httpx (already a project dependency) instead of the Brevo SDK.
When BREVO_API_KEY is not configured the send is skipped with a warning, so
development and tests work without a Brevo account.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_SMTP_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(
    *, to: str, subject: str, html_content: str, text_content: str | None = None
) -> bool:
    """Send one email through Brevo. Returns True when the API accepted it."""
    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        logger.warning("Brevo not configured; skipping email to %s (subject=%r)", to, subject)
        return False

    payload: dict = {
        "sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content

    try:
        resp = httpx.post(
            BREVO_SMTP_URL,
            json=payload,
            headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
            timeout=15.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Brevo send failed for %s: %s", to, exc)
        return False
    return True


def send_verification_email(*, to: str, name: str, verify_url: str) -> bool:
    """Send the 'verify your email' message with a one-click link."""
    expires_hours = max(1, settings.EMAIL_VERIFICATION_EXPIRE_MINUTES // 60)
    subject = "Verify your email address"
    html_content = f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:24px;background:#f5f7fa;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:28px;">
      <h2 style="margin:0 0 12px;color:#1f2933;">Verify your email</h2>
      <p style="color:#3e4c59;line-height:1.5;">Hi {name},</p>
      <p style="color:#3e4c59;line-height:1.5;">
        Welcome! Confirm your email address to activate your account.
      </p>
      <p style="text-align:center;margin:28px 0;">
        <a href="{verify_url}"
           style="background:#2f855a;color:#fff;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;display:inline-block;">
          Verify email
        </a>
      </p>
      <p style="color:#616e7c;font-size:13px;line-height:1.5;">
        This link expires in {expires_hours} hours. If you did not create an account,
        you can safely ignore this email.
      </p>
      <p style="color:#616e7c;font-size:13px;">
        Button not working? Paste this link into your browser:<br>
        <a href="{verify_url}" style="word-break:break-all;color:#2f6fed;">{verify_url}</a>
      </p>
    </div>
  </body>
</html>
"""
    text_content = (
        f"Hi {name},\n\n"
        "Verify your email address to activate your account:\n"
        f"{verify_url}\n\n"
        f"This link expires in {expires_hours} hours. "
        "If you did not create an account, ignore this email."
    )
    return send_email(to=to, subject=subject, html_content=html_content, text_content=text_content)
