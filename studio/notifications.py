"""Submission email notifications for preservation.studio.

Every form submission is saved to the database (reviewable in the Django
admin). When settings.NOTIFY_EMAIL is configured, a plain-text summary of
the submission is also emailed to that address.

Sending is best-effort: if no notify address is set, or the mail server is
unreachable, the submission itself is never affected — the database row is
already saved and the failure is logged.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

SUBMISSION_TITLES = {
    "waitlist": "New waitlist signup",
    "weekend": "New Custom Framing Weekend interest",
    "sentimental": "New Sentimental Value application",
    "intensive": "New Custom Framing Intensive application",
    "contact": "New contact message",
    "sponsor": "New sponsored seat inquiry",
}

# Fields not useful in a review summary.
SKIP_FIELDS = {"id", "created_at", "updated_at"}


def submission_summary(instance):
    """Plain-text, human-readable summary of a submission's fields."""
    lines = []
    for field in instance._meta.fields:
        name = field.name
        if name in SKIP_FIELDS:
            continue
        raw = getattr(instance, name)
        if raw is None or raw == "":
            continue
        if isinstance(raw, bool):
            value = "Yes" if raw else "No"
        elif hasattr(instance, f"get_{name}_display"):
            value = getattr(instance, f"get_{name}_display")()
        elif hasattr(raw, "name") and not isinstance(raw, str):
            # FileField / ImageField — show the stored filename
            value = raw.name
        else:
            value = str(raw)
        lines.append(f"{field.verbose_name}: {value}")
    return "\n".join(lines)


def send_submission_email(kind, instance):
    """Send a summary email for a saved submission. Never raises."""
    recipient = settings.NOTIFY_EMAIL
    if not recipient:
        logger.debug("NOTIFY_EMAIL not configured — skipping %s email", kind)
        return False

    title = SUBMISSION_TITLES.get(kind, "New submission")
    admin_hint = (
        f"Review in the admin: {settings.ADMIN_URL or '(admin disabled)'}"
    )
    subject = f"[preservation.studio] {title}"
    body = (
        f"{title}\n\n"
        f"{submission_summary(instance)}\n\n"
        f"{admin_hint}"
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        logger.info("Sent %s notification to %s", kind, recipient)
        return True
    except Exception:  # noqa: BLE001 — never break a submission over email
        logger.exception("Failed to send %s notification email", kind)
        return False
