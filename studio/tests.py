"""Test suite for preservation.studio.

Runs against SQLite with the local env defaults. The test client pins
HTTP_HOST=localhost because ALLOWED_HOSTS is env-driven and does not
include Django's default 'testserver'.

Nested page structure under test:

  /                           home (waitlist inline)
  /intensive/                 program info        /intensive/apply/    form
  /weekend/                   info + interest list form (inline)
  /sentimental-value/         series info         /sentimental-value/apply/ form
  /about/                     bio + philosophy    /about/faq/          FAQ
  /contact/                   email + message     /contact/sponsor/    sponsor inquiry
"""

from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from .models import (
    ContactMessage,
    IntensiveApplication,
    SentimentalValueApplication,
    WaitlistEntry,
    WeekendInterest,
)

HOST = {"HTTP_HOST": "localhost"}

# (url name, marker that must appear on the page)
PAGES = [
    ("studio:home", "preservation.studio"),
    ("studio:intensive", "Custom Framing Intensive"),
    ("studio:intensive_apply", "Apply to the Intensive"),
    ("studio:weekend", "Custom Framing Weekend"),
    ("studio:sentimental", "Sentimental Value"),
    ("studio:sentimental_apply", "Share your story"),
    ("studio:about", "The studio"),
    ("studio:about_faq", "Frequently asked"),
    ("studio:contact", "Get in touch"),
    ("studio:contact_sponsor", "Sponsor a Seat"),
]


def client():
    return Client(**HOST)


class PageRenderTests(TestCase):
    def test_all_pages_render(self):
        for name, marker in PAGES:
            with self.subTest(page=name):
                resp = client().get(reverse(name))
                self.assertEqual(resp.status_code, 200, name)
                self.assertContains(resp, marker)
                self.assertContains(resp, "preservation.studio")

    def test_every_page_has_studio_title_tag(self):
        """The site title is preservation.studio throughout."""
        for name, _ in PAGES:
            with self.subTest(page=name):
                resp = client().get(reverse(name))
                html = resp.content.decode()
                self.assertIn("<title>", html)
                self.assertIn("preservation.studio", html.split("<title>")[1].split("</title>")[0])

    def test_404_uses_custom_template(self):
        resp = client().get("/no-such-page/")
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "isn't in the archive", status_code=404)

    def test_admin_disabled_when_url_unset(self):
        """With DJANGO_ADMIN_URL unset, /admin/ must not resolve."""
        resp = client().get("/admin/login/")
        self.assertEqual(resp.status_code, 404)


class NestedStructureTests(TestCase):
    """Forms and FAQ live on nested child pages, not inline on parents."""

    def test_intensive_form_is_nested(self):
        parent = client().get(reverse("studio:intensive"))
        self.assertNotContains(parent, 'name="first_name"')
        self.assertContains(parent, reverse("studio:intensive_apply"))
        child = client().get(reverse("studio:intensive_apply"))
        self.assertContains(child, 'name="first_name"')
        self.assertContains(child, 'name="liability_consent"')

    def test_sentimental_form_is_nested(self):
        parent = client().get(reverse("studio:sentimental"))
        self.assertNotContains(parent, 'name="object_description"')
        self.assertContains(parent, reverse("studio:sentimental_apply"))
        child = client().get(reverse("studio:sentimental_apply"))
        self.assertContains(child, 'name="object_description"')
        self.assertContains(child, 'enctype="multipart/form-data"')

    def test_faq_is_nested(self):
        parent = client().get(reverse("studio:about"))
        self.assertNotContains(parent, "<details")
        self.assertContains(parent, reverse("studio:about_faq"))
        child = client().get(reverse("studio:about_faq"))
        self.assertContains(child, "<details")
        self.assertContains(child, "Do I need experience?")

    def test_sponsor_inquiry_is_nested(self):
        parent = client().get(reverse("studio:contact"))
        self.assertContains(parent, reverse("studio:contact_sponsor"))
        child = client().get(reverse("studio:contact_sponsor"))
        self.assertContains(child, 'name="message"')
        self.assertContains(child, "What sponsors receive")

    def test_weekend_interest_form_inline(self):
        """The brief nests no form under Weekend — interest list stays inline."""
        resp = client().get(reverse("studio:weekend"))
        self.assertContains(resp, 'name="city"')

    def test_waitlist_inline_on_home(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, 'name="email"')


class HomePageTests(TestCase):
    """The Home page is labeled in the nav and carries the brief's copy."""

    def test_nav_has_home_link(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, 'href="/"')
        self.assertContains(resp, ">Home</a>")

    def test_brief_intro_copy_present(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, "Come out knowing how to frame the things")
        self.assertContains(resp, "The photo that made it through three moves.")
        self.assertContains(resp, "The letter you've read a hundred times.")

    def test_offering_cards_present(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, "The full trade, start to finish.")
        self.assertContains(resp, "The full curriculum, compressed.")
        self.assertContains(resp, "6 weeks")
        self.assertContains(resp, "2 days")

    def test_sponsor_seat_copy_present(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, "One sponsored seat is available per cohort")
        self.assertContains(resp, "QTPOC artist")

    def test_waitlist_copy_present(self):
        resp = client().get(reverse("studio:home"))
        self.assertContains(resp, "Join the waitlist")
        self.assertContains(resp, "when the next cohort opens")


class WaitlistTests(TestCase):
    def test_valid_submission_saves_and_redirects(self):
        resp = client().post(
            reverse("studio:home"),
            {"email": "artist@example.com"},
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "waitlist"}))
        self.assertEqual(WaitlistEntry.objects.count(), 1)
        self.assertEqual(WaitlistEntry.objects.first().email, "artist@example.com")

    def test_duplicate_email_rejected(self):
        WaitlistEntry.objects.create(email="again@example.com")
        resp = client().post(
            reverse("studio:home"),
            {"email": "again@example.com"},
        )
        self.assertEqual(resp.status_code, 200)  # form re-rendered
        self.assertContains(resp, "already exists")
        self.assertEqual(WaitlistEntry.objects.count(), 1)

    def test_invalid_email_rejected(self):
        resp = client().post(reverse("studio:home"), {"email": "not-an-email"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Enter a valid email")
        self.assertEqual(WaitlistEntry.objects.count(), 0)

    def test_honeypot_trap(self):
        resp = client().post(
            reverse("studio:home"),
            {"email": "bot@example.com", "honeypot": "I am a bot"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(WaitlistEntry.objects.count(), 0)

    def test_thanks_page_shows_waitlist_message(self):
        resp = client().get(reverse("studio:thanks", kwargs={"kind": "waitlist"}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "on the list")


class WeekendInterestTests(TestCase):
    def test_valid_submission_saves(self):
        resp = client().post(
            reverse("studio:weekend"),
            {"name": "Maya Chen", "email": "maya@example.com", "city": "seattle"},
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "weekend"}))
        entry = WeekendInterest.objects.get()
        self.assertEqual(entry.name, "Maya Chen")
        self.assertEqual(entry.city, "seattle")

    def test_city_required(self):
        resp = client().post(
            reverse("studio:weekend"),
            {"name": "Maya Chen", "email": "maya@example.com", "city": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(WeekendInterest.objects.count(), 0)


class SentimentalValueTests(TestCase):
    def test_valid_submission_with_photo_saves(self):
        buf = BytesIO()
        Image.new("RGB", (4, 4), color="#E3B93C").save(buf, format="JPEG")
        img = SimpleUploadedFile(
            "letter.jpg", buf.getvalue(), content_type="image/jpeg"
        )
        resp = client().post(
            reverse("studio:sentimental_apply"),
            {
                "name": "Rosa Diaz",
                "email": "rosa@example.com",
                "instagram": "@rosa",
                "object_description": "A postcard from my grandmother",
                "why_it_matters": "She wrote it the year I was born.",
                "origin": "Handed down from my grandmother.",
                "photo": img,
            },
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "sentimental"}))
        app = SentimentalValueApplication.objects.get()
        self.assertEqual(app.name, "Rosa Diaz")
        self.assertTrue(app.photo.name.startswith("sentimental/"))


class IntensiveApplicationTests(TestCase):
    VALID = {
        "first_name": "Jon",
        "last_name": "Dreksler",
        "email": "jon@example.com",
        "phone": "(310) 555-0100",
        "instagram_or_website": "jdrexx",
        "about_yourself": "I make things with my hands.",
        "prior_experience": "None!",
        "why_framing": "I want to frame my own work.",
        "goals": "Frame my own work.",
        "accommodations": "",
        "questions": "",
        "payment_plan_needed": "on",
        "payment_plan_choice": "option_a",
        "sponsored_seat_consideration": "",
        "sponsored_seat_statement": "",
        "attendance_commitment": "",
        "interview_availability": "Evenings after 6pm, Tuesdays and Thursdays.",
        "interview_format": "video",
        "application_fee_status": "paid",
        "liability_consent": "on",
    }

    def test_full_application_saves(self):
        resp = client().post(reverse("studio:intensive_apply"), self.VALID)
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "intensive"}))
        app = IntensiveApplication.objects.get()
        self.assertEqual(app.first_name, "Jon")
        self.assertTrue(app.payment_plan_needed)
        self.assertEqual(app.payment_plan_choice, "option_a")
        self.assertEqual(app.interview_format, "video")
        self.assertEqual(app.application_fee_status, "paid")
        self.assertTrue(app.liability_consent)

    def test_required_fields_enforced(self):
        resp = client().post(reverse("studio:intensive_apply"), {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_payment_plan_requires_choice(self):
        data = dict(self.VALID)
        data["payment_plan_needed"] = "on"
        data["payment_plan_choice"] = ""
        resp = client().post(reverse("studio:intensive_apply"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please choose a payment plan")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_sponsored_seat_requires_statement(self):
        data = dict(self.VALID)
        data["sponsored_seat_consideration"] = "on"
        data["sponsored_seat_statement"] = ""
        resp = client().post(reverse("studio:intensive_apply"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please share briefly")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_no_payment_plan_ok(self):
        data = dict(self.VALID)
        data["payment_plan_needed"] = ""
        data["payment_plan_choice"] = ""
        resp = client().post(reverse("studio:intensive_apply"), data)
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "intensive"}))
        app = IntensiveApplication.objects.get()
        self.assertFalse(app.payment_plan_needed)


class NotificationTests(TestCase):
    """Every submission emails the notify address when configured, and the
    submission itself never breaks if email fails."""

    EMAIL_SETTINGS = {
        "NOTIFY_EMAIL": "alerts@preservation.studio",
        "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    }

    def test_waitlist_emails_notify_when_configured(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(
                reverse("studio:home"),
                {"email": "notify@example.com"},
            )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "waitlist"}))
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["alerts@preservation.studio"])
        self.assertIn("New waitlist signup", msg.subject)
        self.assertIn("notify@example.com", msg.body)
        self.assertIn("Review in the admin", msg.body)

    def test_intensive_application_emails_full_summary(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(reverse("studio:intensive_apply"), IntensiveApplicationTests.VALID)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn("New Custom Framing Intensive application", msg.subject)
        self.assertIn("Jon", msg.body)
        self.assertIn("Option A", msg.body)
        self.assertIn("Video", msg.body)

    def test_sponsor_inquiry_emails_as_sponsor(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(
                reverse("studio:contact_sponsor"),
                {"name": "A Gallery", "email": "g@example.com",
                 "message": "We'd like to fund a seat."},
            )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New sponsored seat inquiry", mail.outbox[0].subject)

    def test_contact_message_emails_as_contact(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(
                reverse("studio:contact"),
                {"name": "A Friend", "email": "f@example.com",
                 "kind": "general", "message": "When is the next cohort?"},
            )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New contact message", mail.outbox[0].subject)

    def test_no_email_when_notify_unset(self):
        """Default config (no notify address) sends nothing but still saves."""
        resp = client().post(
            reverse("studio:home"),
            {"email": "quiet@example.com"},
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "waitlist"}))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(WaitlistEntry.objects.filter(email="quiet@example.com").count(), 1)

    def test_email_failure_does_not_break_submission(self):
        with self.settings(**self.EMAIL_SETTINGS):
            with mock.patch(
                "studio.notifications.send_mail",
                side_effect=RuntimeError("smtp down"),
            ):
                resp = client().post(
                    reverse("studio:home"),
                    {"email": "brave@example.com"},
                )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "waitlist"}))
        self.assertEqual(WaitlistEntry.objects.filter(email="brave@example.com").count(), 1)


class ContactTests(TestCase):
    def test_general_inquiry_saves(self):
        resp = client().post(
            reverse("studio:contact"),
            {
                "name": "A Friend",
                "email": "friend@example.com",
                "kind": "general",
                "message": "When does the next cohort start?",
            },
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "contact"}))
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.kind, "general")

    def test_email_required(self):
        resp = client().post(
            reverse("studio:contact"),
            {"name": "X", "email": "", "kind": "general", "message": "hi"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_sponsor_inquiry_saves_as_sponsorship(self):
        resp = client().post(
            reverse("studio:contact_sponsor"),
            {
                "name": "A Gallery",
                "email": "gallery@example.com",
                "message": "We'd like to fund a seat for the next cohort.",
            },
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "sponsor"}))
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.kind, "sponsorship")
        self.assertIn("fund a seat", msg.message)
