"""Deployment checks for the submission email path.

Notifications are deliberately best-effort — a dead mail server must never
cost the client a lead. The cost of that choice is that a *permanently*
broken configuration is invisible: submissions keep landing in the admin
while the alert emails stop arriving with nothing on screen to show for it.

So the misconfigurations a human can't see at runtime are boot errors here.
``migrate`` and ``collectstatic`` run system checks, so a bad value fails the
Railway deploy instead of quietly reaching production.
"""

from email.headerregistry import AddressHeader

from django.conf import settings
from django.core.checks import Error, register

# Django permits bare local mailboxes ("From: webmaster"), so this defect is
# not fatal on its own — mirror django.core.mail.backends.smtp.prep_address.
IGNORED_DEFECTS = {"addr-spec local part with no domain"}


@register()
def submission_email_config(app_configs, **kwargs):
    """Fail loudly when notifications are configured but cannot be sent."""
    if not settings.NOTIFY_EMAIL:
        # Notifications are switched off; nothing to validate.
        return []

    problems = []

    if not settings.EMAIL_HOST:
        problems.append(
            Error(
                "DJANGO_NOTIFY_EMAIL is set but DJANGO_EMAIL_HOST is empty — "
                "no mail server to send through.",
                hint="Set DJANGO_EMAIL_HOST (e.g. smtp.mail.me.com for this "
                "domain's iCloud mail) or unset DJANGO_NOTIFY_EMAIL.",
                id="studio.E001",
            )
        )

    # Parse the From header exactly the way the SMTP backend does at send
    # time. An unquoted period in the display name ("preservation.studio
    # <no-reply@...>") is the classic case: it looks fine everywhere and
    # raises ValueError on every single send.
    defects = {
        str(defect)
        for defect in AddressHeader.value_parser(
            settings.DEFAULT_FROM_EMAIL
        ).all_defects
    } - IGNORED_DEFECTS

    if defects:
        problems.append(
            Error(
                f"DJANGO_FROM_EMAIL {settings.DEFAULT_FROM_EMAIL!r} is not a "
                f"valid address: {'; '.join(sorted(defects))}",
                hint="Quote a display name that contains a period "
                '("preservation.studio" <no-reply@preservation.studio>) or '
                "drop the period (Preservation Studio <no-reply@...>).",
                id="studio.E002",
            )
        )

    return problems
