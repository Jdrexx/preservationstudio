"""Signal wiring — email notifications on new submissions.

Fires only for newly created rows (created=True), so editing an existing
submission in the admin does not re-send anything.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    ContactMessage,
    IntensiveApplication,
    SentimentalValueApplication,
    WaitlistEntry,
    WeekendInterest,
)
from .notifications import send_submission_email

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WaitlistEntry)
def _notify_waitlist(sender, instance, created, **kwargs):
    if created:
        send_submission_email("waitlist", instance)


@receiver(post_save, sender=WeekendInterest)
def _notify_weekend(sender, instance, created, **kwargs):
    if created:
        send_submission_email("weekend", instance)


@receiver(post_save, sender=SentimentalValueApplication)
def _notify_sentimental(sender, instance, created, **kwargs):
    if created:
        send_submission_email("sentimental", instance)


@receiver(post_save, sender=IntensiveApplication)
def _notify_intensive(sender, instance, created, **kwargs):
    if created:
        send_submission_email("intensive", instance)


@receiver(post_save, sender=ContactMessage)
def _notify_contact(sender, instance, created, **kwargs):
    if created:
        # ContactMessage serves both the contact page and the sponsored
        # seat inquiry — the kind field tells us which.
        kind = "sponsor" if instance.kind == "sponsorship" else "contact"
        send_submission_email(kind, instance)
