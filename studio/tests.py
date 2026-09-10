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
from pathlib import Path
import re
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
                self.assertIn(
                    "preservation.studio", html.split("<title>")[1].split("</title>")[0]
                )

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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "waitlist"})
        )
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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "sentimental"})
        )
        app = SentimentalValueApplication.objects.get()
        self.assertEqual(app.name, "Rosa Diaz")
        self.assertTrue(app.photo.name.startswith("sentimental/"))

    def test_phone_sized_photo_submits(self):
        """A real phone photo (~3-6 MB) must not hit Django's request-body cap.

        Regression: DATA_UPLOAD_MAX_MEMORY_SIZE defaults to 2.5 MB, which caps
        the WHOLE multipart body — submissions with an ordinary photo over
        ~2.4 MB failed with a bare 400 and the story was lost. The setting is
        raised to 12 MB; this test proves an ~4 MB upload goes through.
        """
        from os import urandom

        noise = Image.frombytes("RGB", (2200, 2200), urandom(2200 * 2200 * 3))
        buf = BytesIO()
        noise.save(buf, format="JPEG", quality=90)
        assert buf.tell() > 3 * 1024 * 1024  # sanity: this really is a big photo
        img = SimpleUploadedFile(
            "phone-photo.jpg", buf.getvalue(), content_type="image/jpeg"
        )
        resp = client().post(
            reverse("studio:sentimental_apply"),
            {
                "name": "Jordan Lee",
                "email": "jordan@example.com",
                "object_description": "A camera from my grandfather",
                "why_it_matters": "It started my love of photography.",
                "origin": "Handed down.",
                "photo": img,
            },
        )
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "sentimental"})
        )
        app = SentimentalValueApplication.objects.get(name="Jordan Lee")
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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "intensive"})
        )
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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "intensive"})
        )
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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "waitlist"})
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["alerts@preservation.studio"])
        self.assertIn("New waitlist signup", msg.subject)
        self.assertIn("notify@example.com", msg.body)
        self.assertIn("Review in the admin", msg.body)

    def test_intensive_application_emails_full_summary(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(
                reverse("studio:intensive_apply"), IntensiveApplicationTests.VALID
            )
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
                {
                    "name": "A Gallery",
                    "email": "g@example.com",
                    "message": "We'd like to fund a seat.",
                },
            )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New sponsored seat inquiry", mail.outbox[0].subject)

    def test_contact_message_emails_as_contact(self):
        with self.settings(**self.EMAIL_SETTINGS):
            resp = client().post(
                reverse("studio:contact"),
                {
                    "name": "A Friend",
                    "email": "f@example.com",
                    "kind": "general",
                    "message": "When is the next cohort?",
                },
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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "waitlist"})
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(
            WaitlistEntry.objects.filter(email="quiet@example.com").count(), 1
        )

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
        self.assertRedirects(
            resp, reverse("studio:thanks", kwargs={"kind": "waitlist"})
        )
        self.assertEqual(
            WaitlistEntry.objects.filter(email="brave@example.com").count(), 1
        )


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


class SubmissionEmailConfigTests(TestCase):
    """The boot check that keeps a silently-dead email config out of prod.

    Sending is best-effort, so a From address the SMTP backend rejects would
    otherwise fail invisibly on every submission.
    """

    def run_check(self, **settings_overrides):
        from django.core.checks import run_checks

        with self.settings(**settings_overrides):
            return [e for e in run_checks() if e.id.startswith("studio.E")]

    def test_quiet_when_notifications_unset(self):
        """The current live config (no notify address) must never error."""
        self.assertEqual(self.run_check(NOTIFY_EMAIL=""), [])

    def test_default_from_address_is_valid(self):
        """The shipped default must survive the SMTP backend's parser."""
        from django.conf import settings

        errors = self.run_check(
            NOTIFY_EMAIL="alerts@example.com", EMAIL_HOST="smtp.example.com"
        )
        self.assertEqual(errors, [], f"default From rejected: {errors}")
        self.assertEqual(
            settings.DEFAULT_FROM_EMAIL,
            "Preservation Studio <no-reply@preservation.studio>",
        )

    def test_unquoted_period_in_display_name_is_an_error(self):
        """'preservation.studio <...>' raises ValueError at send time."""
        errors = self.run_check(
            NOTIFY_EMAIL="alerts@example.com",
            EMAIL_HOST="smtp.example.com",
            DEFAULT_FROM_EMAIL="preservation.studio <no-reply@preservation.studio>",
        )
        self.assertEqual([e.id for e in errors], ["studio.E002"])
        self.assertIn("period in 'phrase'", errors[0].msg)
        self.assertIn("Quote a display name", errors[0].hint)

    def test_quoted_period_is_accepted(self):
        errors = self.run_check(
            NOTIFY_EMAIL="alerts@example.com",
            EMAIL_HOST="smtp.example.com",
            DEFAULT_FROM_EMAIL='"preservation.studio" <no-reply@preservation.studio>',
        )
        self.assertEqual(errors, [])

    def test_missing_mail_host_is_an_error(self):
        errors = self.run_check(NOTIFY_EMAIL="alerts@example.com", EMAIL_HOST="")
        self.assertEqual([e.id for e in errors], ["studio.E001"])

    def test_from_address_survives_the_real_smtp_backend_parser(self):
        """Same call the SMTP backend makes in _send() — no mock, no socket."""
        from django.core.mail.backends.smtp import EmailBackend

        from django.conf import settings

        backend = EmailBackend()
        for address in (
            settings.DEFAULT_FROM_EMAIL,
            "Preservation Studio <no-reply@preservation.studio>",
            '"preservation.studio" <no-reply@preservation.studio>',
        ):
            with self.subTest(address=address):
                self.assertTrue(backend.prep_address(address))
        with self.assertRaises(ValueError):
            backend.prep_address("preservation.studio <no-reply@preservation.studio>")


class IsThisForYouTests(TestCase):
    """The 'Is this for you?' grid, recreated from Asher's Canva mockup."""

    LEADS = [
        "I want to learn a trade.",
        "I want to make something that lasts.",
        "I want to finally frame the things I've been saving.",
        "I want to make things with my hands.",
        "I want to understand the stories behind what we keep.",
        "I want to frame my own work.",
    ]

    def test_intensive_page_carries_the_grid(self):
        resp = client().get(reverse("studio:intensive"))
        self.assertContains(resp, "Is this for you?")
        self.assertContains(resp, 'class="for-you"')
        for lead in self.LEADS:
            with self.subTest(lead=lead):
                self.assertContains(resp, lead)

    def test_each_lead_has_supporting_copy(self):
        resp = client().get(reverse("studio:intensive"))
        self.assertEqual(
            resp.content.decode().count('class="for-you-item"'), len(self.LEADS)
        )

    def test_section_numbers_stay_sequential(self):
        html = client().get(reverse("studio:intensive")).content.decode()
        numbers = re.findall(r"№ (\d\d) — ", html)
        self.assertEqual(numbers, ["01", "02", "03", "04", "05"])


class DesignLibraryTests(TestCase):
    """The self-hosted font library and the tuner's looks must stay in sync.

    Guards the documented workflow for swapping a free stand-in for a
    purchased webfont: drop the woff2 in, add the @font-face, add the
    option, mirror it in STACKS — and this suite tells you which step
    you skipped.
    """

    static = Path(__file__).resolve().parent / "static" / "studio"

    SYSTEM = {
        "Georgia",
        "Times New Roman",
        "Arial",
        "Helvetica Neue",
        "Courier New",
        "ui-monospace",
        "monospace",
        "sans-serif",
        "serif",
        "cursive",
    }

    def read(self, *parts):
        return self.static.joinpath(*parts).read_text(encoding="utf-8")

    def declared_families(self):
        return set(
            re.findall(r'font-family:\s*"([^"]+)"', self.read("css", "fonts.css"))
        )

    def js_block(self, marker, end="\n  ];"):
        js = self.read("js", "vibe-tuner.js")
        return js.split(marker, 1)[1].split(end, 1)[0]

    def test_every_font_file_referenced_exists(self):
        refs = re.findall(r'url\("\.\./fonts/([^"]+)"\)', self.read("css", "fonts.css"))
        self.assertGreater(len(refs), 25)
        for name in refs:
            with self.subTest(font=name):
                self.assertTrue((self.static / "fonts" / name).is_file(), name)

    def test_no_orphan_font_files_on_disk(self):
        css = self.read("css", "fonts.css")
        for path in sorted((self.static / "fonts").glob("*.woff2")):
            with self.subTest(font=path.name):
                self.assertIn(path.name, css)

    def test_every_tuner_stack_family_is_available(self):
        declared = self.declared_families()
        stacks = self.js_block("var STACKS =", "\n  };")
        # Every stack string may carry fallbacks ("Georgia, serif") — only the
        # first family in each is the one that has to actually be available.
        firsts = {
            chunk.split(",")[0].replace('"', "").replace("'", "").strip()
            for chunk in re.findall(r'"([A-Z][^"]*)"', stacks)
        }
        self.assertTrue(firsts)
        for family in sorted(firsts - self.SYSTEM):
            with self.subTest(family=family):
                self.assertIn(family, declared)

    def test_every_tuner_select_option_resolves_to_a_stack(self):
        html = self.read(
            "..", "..", "templates", "studio", "partials", "vibe_tuner.html"
        )
        for kind in ("display", "body", "mono", "hand"):
            stacks = (
                self.js_block("var STACKS =", "\n  };")
                .split(kind + ": {", 1)[1]
                .split("},", 1)[0]
            )
            options = re.findall(
                r'<option value="(\w+)">',
                html.split('id="vibe-sel-' + kind + '"', 1)[1].split("</select>", 1)[0],
            )
            self.assertTrue(options, kind)
            for key in options:
                with self.subTest(kind=kind, key=key):
                    self.assertIn(key + ":", stacks)

    def test_every_look_preset_is_complete(self):
        token_names = re.findall(r'\["([a-z\-]+)", "', self.js_block("var TOKENS ="))
        slider_names = [
            "--" + name
            for name in re.findall(r'\["([a-z\-]+)", "', self.js_block("var SLIDERS ="))
        ]
        self.assertEqual(len(token_names), 16)
        self.assertEqual(len(slider_names), 7)

        chunks = (
            self.read("js", "vibe-tuner.js")
            .split("var PRESETS =", 1)[1]
            .split('id: "')[1:]
        )
        self.assertEqual(len(chunks), 5)
        for chunk in chunks:
            preset = chunk.split('"', 1)[0]
            tokens = chunk.split("tokens: {", 1)[1].split("},", 1)[0]
            sliders = chunk.split("sliders: {", 1)[1].split("},", 1)[0]
            stacks = chunk.split("stacks: {", 1)[1].split("},", 1)[0]
            with self.subTest(preset=preset):
                for name in token_names:
                    self.assertRegex(
                        tokens, r'"?%s"?: "#[0-9a-f]{6}"' % re.escape(name)
                    )
                for name in slider_names:
                    self.assertIn('"%s"' % name, sliders)
                for var in ("--display", "--serif", "--mono", "--hand"):
                    self.assertIn(var, stacks)

    def test_on_butter_is_a_real_token(self):
        """--on-butter replaced a hard-coded #fdf8ef so a light accent works."""
        site = self.read("css", "site.css")
        self.assertIn("--on-butter:", site)
        rule = site.split(".btn-yellow {")[-1].split("}", 1)[0]
        self.assertIn("color: var(--on-butter)", rule)
        self.assertIn('"on-butter"', self.read("js", "vibe-tuner.js"))

    def test_every_letter_spacing_rule_supports_live_tracking(self):
        """The tuner's Letter spacing dial is --ls-tune, added to every
        non-zero letter-spacing via calc(). A raw (unwrapped) value would
        silently ignore the dial, so any that appear must be flagged here."""
        site = self.read("css", "site.css")
        self.assertIn("--ls-tune: 0em;", site)
        raws = re.findall(r"letter-spacing:\s*([^;]+);", site)
        self.assertGreater(len(raws), 30)
        for value in raws:
            with self.subTest(value=value.strip()):
                if value.strip() != "0":
                    self.assertIn("var(--ls-tune", value)
        # the dial itself: present in the panel, the SLIDERS table, the
        # export block's slider list, and complete in every preset
        html = self.read("..", "..", "templates", "studio", "partials", "vibe_tuner.html")
        self.assertIn('id="vibe-ls-tune"', html)
        self.assertIn('id="out-ls-tune"', html)
        js = self.read("js", "vibe-tuner.js")
        sliders = self.js_block("var SLIDERS =")
        self.assertIn('"ls-tune"', sliders)
        self.assertIn('"em"', sliders)
        self.assertIn('"--ls-tune"', self.js_block("function buildExport"))
        for chunk in js.split('id: "')[1:]:
            preset = chunk.split('"', 1)[0]
            with self.subTest(preset=preset):
                sliders = chunk.split("sliders: {", 1)[1].split("},", 1)[0]
                self.assertIn('"--ls-tune"', sliders)


class TemplateHygieneTests(TestCase):
    """A Django `{# ... #}` comment is SINGLE-LINE ONLY.

    Only the text up to the end of that line is consumed, so a multi-line one
    leaks its 2nd..nth lines AND the trailing `#}` into the rendered page as
    visible copy. This shipped once (a design note appeared verbatim in the
    "Kept" section of the home page), so it is checked both in the source and
    in the rendered output of every route.
    """

    templates = Path(__file__).resolve().parent / "templates"

    def test_no_multiline_single_line_comments_in_templates(self):
        offenders = []
        for path in sorted(self.templates.rglob("*.html")):
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                for m in re.finditer(r"\{#", line):
                    if "#}" in line[m.end() :]:
                        continue
                    offenders.append(f"{path.name}:{i}")
        self.assertEqual(
            offenders,
            [],
            "multi-line {# #} comments leak into the page — use a comment block",
        )

    def test_no_template_syntax_leaks_into_rendered_pages(self):
        """Nothing that looks like template syntax may reach the browser."""
        pages = [
            ("studio:home", {}),
            ("studio:intensive", {}),
            ("studio:intensive_apply", {}),
            ("studio:weekend", {}),
            ("studio:sentimental", {}),
            ("studio:sentimental_apply", {}),
            ("studio:about", {}),
            ("studio:about_faq", {}),
            ("studio:contact", {}),
            ("studio:contact_sponsor", {}),
            ("studio:thanks", {"kind": "waitlist"}),
        ]
        for name, kwargs in pages:
            resp = client().get(reverse(name, kwargs=kwargs or None))
            body = resp.content.decode()
            with self.subTest(page=name):
                self.assertEqual(resp.status_code, 200)
                for token in ("{#", "#}", "{%", "{{"):
                    self.assertNotIn(token, body, f"{token} leaked into {name}")


class TrackCompositionTests(TestCase):
    """The site is ONE page in the rabenrifaie.com composition.

    Read off the reference's live DOM: a fixed UI at the edges over
    full-viewport scenes (100vw x 100svh) laid out side by side, with the
    document clipped so nothing scrolls vertically, and one scene per nav
    item. The CSS half of that contract is checked here too — a template
    test alone would not notice the layout drifting back to stacked pages.
    """

    static = Path(__file__).resolve().parent / "static" / "studio"

    # one scene per nav item, in order
    NAV = ["home", "intensive", "weekend", "sentimental-value", "about", "contact"]

    def home(self):
        return client().get(reverse("studio:home")).content.decode()

    def css(self):
        return (self.static / "css" / "site.css").read_text(encoding="utf-8")

    def test_one_scene_per_nav_item(self):
        html = self.home()
        self.assertEqual(html.count('class="scene"'), len(self.NAV))
        for scene_id in self.NAV:
            with self.subTest(scene=scene_id):
                self.assertIn('id="%s"' % scene_id, html)

    def test_scene_bar_links_point_at_scenes(self):
        html = self.home()
        for scene_id in self.NAV:
            with self.subTest(scene=scene_id):
                self.assertIn('href="#%s" data-scene-link' % scene_id, html)

    def test_document_is_clipped_and_the_track_is_the_only_scroller(self):
        css = self.css()
        body = css.split("body.is-track {", 1)[1].split("}", 1)[0]
        self.assertIn("height: 100svh", body)
        self.assertIn("overflow: hidden", body)
        scene = css.split("\n.scene {", 1)[1].split("}", 1)[0]
        self.assertIn("width: 100vw", scene)
        self.assertIn("height: 100svh", scene)

    def test_scenes_stay_one_viewport_wide_on_small_screens(self):
        """One structure at every width, as the reference has it."""
        block = self.css().split("/* ---------- Track responsive", 1)[1]
        block = block.split("@media (max-width: 900px) {", 1)[1]
        block = block.split("@media (prefers-reduced-motion", 1)[0]
        self.assertNotIn("flex-direction: column", block)
        self.assertNotIn("height: auto", block)

    def test_every_scene_keeps_a_heading_and_a_destination(self):
        html = self.home()
        self.assertEqual(html.count('class="scene-cta pill"'), len(self.NAV))
        self.assertEqual(html.count("<h1"), 1)
        self.assertEqual(html.count("<h2"), len(self.NAV) - 1)
        self.assertIn("studio/js/track", html)

    def test_track_controls_are_present(self):
        html = self.home()
        for hook in ("data-explore", "data-scene-now", "data-scene-total"):
            with self.subTest(hook=hook):
                self.assertIn(hook, html)
        self.assertIn("data-track-prev", html)
        self.assertIn("data-track-next", html)


class WelcomeGateTests(TestCase):
    """The entry screen, replicated from the reference's welcome overlay.

    Read off its live DOM: a full-bleed surface, a small flat progress bar
    dead centre, a percentage counting up bottom-right in an italic serif, and
    at 100% the bar gives way to the studio name with a pill-outlined
    "Welcome". The safety half matters as much as the look: a gate whose only
    exit is scripted traps anyone whose script did not run, so the no-JS rule
    and the CSS failsafe are asserted here alongside the visuals.
    """

    static = Path(__file__).resolve().parent / "static" / "studio"

    def home(self):
        return client().get(reverse("studio:home")).content.decode()

    def css(self):
        return (self.static / "css" / "site.css").read_text(encoding="utf-8")

    def js(self):
        return (self.static / "js" / "welcome.js").read_text(encoding="utf-8")

    def test_gate_is_on_the_track_page(self):
        html = self.home()
        self.assertIn('id="welcome"', html)
        self.assertIn('role="progressbar"', html)
        self.assertIn('id="welcome-count">0<', html)
        self.assertIn('id="welcome-enter"', html)
        self.assertIn(">Welcome</button>", html)

    def test_the_bar_is_the_wordmark_itself(self):
        """The reference's bar is its title's letterforms, not a rectangle.

        Read off their DOM: a white plane scaled from the centre under a black
        panel masked by an SVG of the wordmark, so the title is what fills in.
        Ours paints the wordmark in two layers clipped to its own glyphs, the
        solid one sized by --fill.
        """
        css = self.css()
        name = css.split(".welcome-name {", 1)[1].split("}", 1)[0]
        self.assertIn("background-clip: text", name)
        self.assertIn("-webkit-background-clip: text", name)
        self.assertIn("var(--fill) 100%", name)
        # grown from the middle, as their centre-origin transform does
        self.assertIn("50% 50%", name)
        self.assertIn("--fill: 0%", name)
        # no rectangular track/fill left anywhere
        self.assertEqual(css.count(".welcome-bar"), 0)
        self.assertNotIn('class="welcome-bar"', self.home())

    def test_the_bar_element_is_real_text(self):
        """Real selectable text, but not the page's h1 — the gate is transient."""
        html = self.home()
        self.assertIn('<p class="welcome-name" id="welcome-name">preservation', html)
        css = self.css()
        name = css.split(".welcome-name {", 1)[1].split("}", 1)[0]
        self.assertNotIn("font-size: 0", name)

    def test_progress_is_reported_for_screen_readers(self):
        """The visible bar is the wordmark, so the value rides on a hidden node."""
        html = self.home()
        self.assertIn('class="welcome-visually-hidden"', html)
        self.assertIn('role="progressbar"', html)
        css = self.css()
        hidden = css.split(".welcome-visually-hidden {", 1)[1].split("}", 1)[0]
        self.assertIn("clip-path: inset(50%)", hidden)

    def test_gate_carries_the_studio_name_not_the_reference_s(self):
        html = self.home()
        self.assertIn('id="welcome-name"', html)
        self.assertNotIn("RabenRifaie", html)

    def test_gate_ships_disabled_until_the_script_ready_s_it(self):
        """The Welcome button must not be pressable during the count."""
        self.assertIn('id="welcome-enter" disabled', self.home())
        self.assertIn("enter.disabled = false", self.js())

    def test_noscript_hides_the_gate(self):
        html = self.home()
        self.assertIn(
            "<noscript><style>.welcome { display: none; }</style></noscript>", html
        )

    def test_css_carries_a_failsafe_for_a_script_that_never_runs(self):
        css = self.css()
        self.assertIn("welcome-failsafe", css)
        # the JS cancels it, so a working page never self-dismisses
        self.assertIn(".welcome.is-live", css)
        self.assertIn('gate.classList.add("is-live")', self.js())

    def test_gate_sits_above_the_fixed_ui(self):
        css = self.css()
        gate = css.split(".welcome {", 1)[1].split("}", 1)[0]
        self.assertIn("position: fixed", gate)
        self.assertIn("inset: 0", gate)
        self.assertIn("z-index: 90", gate)
        # the header and the scene bar are z-index 60
        self.assertLess(60, 90)

    def test_gate_locks_the_page_underneath(self):
        css = self.css()
        self.assertIn("body.is-welcome .track", css)
        self.assertIn("pointer-events: none", css)
        self.assertIn('body.classList.add("is-welcome")', self.js())

    def test_track_ignores_the_keyboard_while_the_gate_is_up(self):
        track = (self.static / "js" / "track.js").read_text(encoding="utf-8")
        guard = 'if (document.body.classList.contains("is-welcome")) return;'
        self.assertIn(guard, track)

    def test_leaving_removes_the_node(self):
        """A hidden z-index-90 overlay is still a screen-reader and click trap."""
        self.assertIn("removeChild(gate)", self.js())
        self.assertIn('gate.classList.add("is-leaving")', self.js())

    def test_reduced_motion_skips_the_count_and_the_fade(self):
        self.assertIn("prefers-reduced-motion", self.css())
        self.assertIn("reduce.matches", self.js())

    def test_gate_is_only_on_the_track_page(self):
        for name in ("studio:intensive", "studio:about", "studio:contact"):
            with self.subTest(page=name):
                html = client().get(reverse(name)).content.decode()
                self.assertNotIn('id="welcome"', html)
                self.assertNotIn("welcome.js", html)

    def test_script_is_loaded_after_the_track(self):
        html = self.home()
        self.assertIn("studio/js/welcome", html)
        self.assertLess(html.index("studio/js/track"), html.index("studio/js/welcome"))
