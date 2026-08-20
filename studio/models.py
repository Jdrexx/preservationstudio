"""Data models for preservation.studio.

Every form on the site lands in the database so the studio can review
applications, waitlist signups, weekend interest, and sponsor inquiries
from one place (the Django admin).
"""

from django.db import models


class BaseSubmission(models.Model):
    """Shared bookkeeping for every submission."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class WaitlistEntry(BaseSubmission):
    """Home page waitlist — people interested in future cohorts."""

    email = models.EmailField(unique=True)

    class Meta(BaseSubmission.Meta):
        verbose_name_plural = "waitlist entries"

    def __str__(self):
        return self.email


class WeekendInterest(BaseSubmission):
    """Custom Framing Weekend interest list with city dropdown."""

    CITY_CHOICES = [
        ("new_york", "New York"),
        ("new_jersey", "New Jersey"),
        ("philadelphia", "Philadelphia"),
        ("seattle", "Seattle"),
        ("albuquerque", "Albuquerque"),
        ("santa_fe", "Santa Fe"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    city = models.CharField(max_length=40, choices=CITY_CHOICES)

    class Meta(BaseSubmission.Meta):
        verbose_name_plural = "weekend interest entries"

    def __str__(self):
        return f"{self.name} — {self.get_city_display()}"


class SentimentalValueApplication(BaseSubmission):
    """Sentimental Value series — object stories + photo upload."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    instagram = models.CharField(max_length=120, blank=True)
    object_description = models.TextField(verbose_name="What is the object?")
    why_it_matters = models.TextField(verbose_name="Why does it matter to you?")
    origin = models.TextField(
        verbose_name="Who does it belong to or where did it come from?"
    )
    photo = models.ImageField(
        upload_to="sentimental/",
        blank=True,
        verbose_name="Photo of the object",
    )

    class Meta(BaseSubmission.Meta):
        verbose_name_plural = "sentimental value applications"

    def __str__(self):
        return f"{self.name} — {self.object_description[:60]}"


class IntensiveApplication(BaseSubmission):
    """Custom Framing Intensive application — the full form."""

    # ---- Application -------------------------------------------------
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    instagram_or_website = models.CharField(max_length=200, blank=True)
    about_yourself = models.TextField()
    prior_experience = models.TextField()
    why_framing = models.TextField()
    goals = models.TextField()
    accommodations = models.TextField(blank=True)
    questions = models.TextField(blank=True)

    # ---- Payment ------------------------------------------------------
    payment_plan_needed = models.BooleanField(
        default=False, verbose_name="Will you need a payment plan?"
    )
    PAYMENT_PLAN_CHOICES = [
        ("option_a", "Option A — $550 / $1,000 / $1,050 (total $2,550)"),
        ("option_b", "Option B — $500 / $700 / $700 / $650 (total $2,550)"),
    ]
    payment_plan_choice = models.CharField(
        max_length=20, choices=PAYMENT_PLAN_CHOICES, blank=True
    )

    # ---- Sponsored seat ------------------------------------------------
    sponsored_seat_consideration = models.BooleanField(
        default=False,
        verbose_name="Would you like to be considered for the sponsored seat?",
    )
    sponsored_seat_statement = models.TextField(blank=True)
    attendance_commitment = models.TextField(blank=True)

    # ---- Interview -----------------------------------------------------
    interview_availability = models.TextField(
        verbose_name="What days and times work best for a 10-minute call?"
    )
    INTERVIEW_FORMAT_CHOICES = [
        ("video", "Video"),
        ("phone", "Phone"),
    ]
    interview_format = models.CharField(
        max_length=10, choices=INTERVIEW_FORMAT_CHOICES
    )

    # ---- Application fee ------------------------------------------------
    FEE_STATUS_CHOICES = [
        ("paid", "Yes, I've submitted the fee"),
        ("no", "No, not yet"),
        ("waiver", "I have requested a fee waiver"),
    ]
    application_fee_status = models.CharField(
        max_length=10, choices=FEE_STATUS_CHOICES
    )

    # ---- Liability ------------------------------------------------------
    liability_consent = models.BooleanField(
        default=False,
        verbose_name="I understand the liability waiver requirement and am ready to sign",
    )

    class Meta(BaseSubmission.Meta):
        verbose_name_plural = "intensive applications"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ContactMessage(BaseSubmission):
    """Sponsor / private workshop / general inquiries from the Contact page."""

    KIND_CHOICES = [
        ("general", "General question"),
        ("private", "Private session or corporate workshop"),
        ("sponsorship", "Sponsorship"),
    ]
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="general")
    message = models.TextField()

    class Meta(BaseSubmission.Meta):
        verbose_name_plural = "contact messages"

    def __str__(self):
        return f"{self.get_kind_display()} — {self.email}"
