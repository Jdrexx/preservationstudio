"""Test suite for preservation.studio.

Runs against SQLite with the local env defaults. The test client pins
HTTP_HOST=localhost because ALLOWED_HOSTS is env-driven and does not
include Django's default 'testserver'.
"""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
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

PAGES = [
    ("studio:home", "preservation.studio"),
    ("studio:intensive", "Custom Framing Intensive"),
    ("studio:weekend", "Custom Framing Weekend"),
    ("studio:sentimental", "Sentimental Value"),
    ("studio:about", "The studio"),
    ("studio:contact", "Get in touch"),
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
            reverse("studio:sentimental"),
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
        resp = client().post(reverse("studio:intensive"), self.VALID)
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "intensive"}))
        app = IntensiveApplication.objects.get()
        self.assertEqual(app.first_name, "Jon")
        self.assertTrue(app.payment_plan_needed)
        self.assertEqual(app.payment_plan_choice, "option_a")
        self.assertEqual(app.interview_format, "video")
        self.assertEqual(app.application_fee_status, "paid")
        self.assertTrue(app.liability_consent)

    def test_required_fields_enforced(self):
        resp = client().post(reverse("studio:intensive"), {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_payment_plan_requires_choice(self):
        data = dict(self.VALID)
        data["payment_plan_needed"] = "on"
        data["payment_plan_choice"] = ""
        resp = client().post(reverse("studio:intensive"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please choose a payment plan")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_sponsored_seat_requires_statement(self):
        data = dict(self.VALID)
        data["sponsored_seat_consideration"] = "on"
        data["sponsored_seat_statement"] = ""
        resp = client().post(reverse("studio:intensive"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please share briefly")
        self.assertEqual(IntensiveApplication.objects.count(), 0)

    def test_no_payment_plan_ok(self):
        data = dict(self.VALID)
        data["payment_plan_needed"] = ""
        data["payment_plan_choice"] = ""
        resp = client().post(reverse("studio:intensive"), data)
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "intensive"}))
        app = IntensiveApplication.objects.get()
        self.assertFalse(app.payment_plan_needed)


class ContactTests(TestCase):
    def test_sponsorship_inquiry_saves(self):
        resp = client().post(
            reverse("studio:contact"),
            {
                "name": "A Gallery",
                "email": "gallery@example.com",
                "kind": "sponsorship",
                "message": "We'd like to fund a seat.",
            },
        )
        self.assertRedirects(resp, reverse("studio:thanks", kwargs={"kind": "contact"}))
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.kind, "sponsorship")
        self.assertEqual(msg.message, "We'd like to fund a seat.")

    def test_email_required(self):
        resp = client().post(
            reverse("studio:contact"),
            {"name": "X", "email": "", "kind": "general", "message": "hi"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
