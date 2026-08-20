# preservation.studio

Website for **Preservation Studio** — a custom framing program and preservation studio
based in Los Angeles, founded by Asher Cano.

Built with **Python / Django 6**. Deployed on **Railway**. Repo: `Jdrexx/preservationstudio`.

## Pages (launch version)

Nested page layout — parent pages hold the info, child pages hold the forms.

| Route | Page | Nested |
|---|---|---|
| `/` | Home — hero, offerings, sponsor a seat | Waitlist form (inline) |
| `/intensive/` | Custom Framing Intensive — sessions, pricing | `/intensive/apply/` — full application |
| `/weekend/` | Custom Framing Weekend — cities, interest list | Interest form (inline) |
| `/sentimental-value/` | Sentimental Value series | `/sentimental-value/apply/` — object story + photo |
| `/about/` | Bio, philosophy | `/about/faq/` — FAQ |
| `/contact/` | Email, Instagram, message form | `/contact/sponsor/` — sponsored seat inquiry |

Every submission is stored in the database and reviewed in the Django admin
(admin is mounted at a secret path set by `DJANGO_ADMIN_URL` — unset = admin disabled).

## Submission notifications (email + admin)

Every inquiry is **always** saved to the database and visible in the admin —
the email is an extra alert on top.

| Submission | Admin model | Email subject |
|---|---|---|
| Home waitlist | `WaitlistEntry` | New waitlist signup |
| Weekend interest | `WeekendInterest` | New Custom Framing Weekend interest |
| Intensive application | `IntensiveApplication` | New Custom Framing Intensive application |
| Sentimental Value application | `SentimentalValueApplication` | New Sentimental Value application |
| Contact message | `ContactMessage` | New contact message |
| Sponsor seat inquiry | `ContactMessage` (kind=sponsorship) | New sponsored seat inquiry |

To receive email alerts, set on Railway:

| Variable | Example | Purpose |
|---|---|---|
| `DJANGO_NOTIFY_EMAIL` | `alerts@yourdomain.com` | Where summaries are sent. Empty/unset = no emails, submissions still saved |
| `DJANGO_EMAIL_HOST` | `smtp.gmail.com` / `smtp.sendgrid.net` / `smtp.resend.com` | SMTP server of any provider |
| `DJANGO_EMAIL_PORT` | `587` | SMTP port (default 587) |
| `DJANGO_EMAIL_USER` | your SMTP username | |
| `DJANGO_EMAIL_PASSWORD` | your SMTP password | |
| `DJANGO_EMAIL_USE_TLS` | `1` | TLS on (default) |
| `DJANGO_FROM_EMAIL` | `preservation.studio <no-reply@...>` | From address (optional) |

Email sending is best-effort: if the mail server is unreachable the submission
still saves and the visitor still sees the thank-you page (failure is logged).

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

- **Database:** SQLite locally; Postgres on Railway (via `DATABASE_URL`).
- **Static:** Whitenoise with `CompressedManifestStaticFilesStorage` — bump the `?v=` on
  `site.css` in `base.html` when shipping CSS changes.

## Environment variables (Railway)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Production secret — required |
| `DJANGO_DEBUG` | `0` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated, e.g. `preservation.studio,.up.railway.app` |
| `DJANGO_ADMIN_URL` | Secret admin path, e.g. `studio-admin` → `/studio-admin/` |
| `DATABASE_URL` | Postgres connection string (Railway injects) |

## Client placeholders to replace

- Contact email is set to `hello@preservation.studio` (footer, contact, forms).
- Instagram handle is set to `@preservation.studio`.
- The Venmo / payment link in the intensive application is not wired up yet —
  the form currently records fee status only.
- About page portrait is a styled placeholder frame — drop in a real photo when ready.

## Design system: typography & palette

All styling is driven by CSS variables in the `:root` block of
`studio/static/studio/css/site.css` — one place to restyle the whole site.

**Fonts** (self-hosted in `studio/static/studio/fonts/`, no Google CDN dependency):

| Role | Font | Notes |
|---|---|---|
| Display (headlines) | **Fraunces** | Variable: optical size, weight, SOFT, WONK |
| Body | **Newsreader** | Long-form reading |
| Labels / institution | **IBM Plex Mono** | Nav, buttons, section numbers |
| Handwritten notes | **Kalam** (alt: Caveat) | Hero annotation accents |

**Palette** (client's PANTONE-anchored hexes):

| Token | Hex | Use |
|---|---|---|
| `--paper` | `#F5EDD6` Papyrus | Page background |
| `--paper-deep` | `#D5D5BC` Pearl | Alternate section bands |
| `--card` | `#FFFAE6` Butter | Cards, form panels |
| `--ink` | `#24140C` Licorice | Text |
| `--ink-soft` | `#5F5A41` Olive Night | Labels, captions |
| `--rule-strong` | `#B3A189` Cinnamon | Borders, rules |
| `--butter` | `#FFDE8A` Honey | Accent, buttons, highlights |
| `--blue` | `#9EBEC6` Light Blue | Weekend card, sponsor band |
| `--plum` | `#3D2D2E` Chocolate Plum | Footer |

## Vibe tuner (?vibe=1)

A hidden design room for tuning the look live. Visitors never see it.

- **Open it:** append `?vibe=1` to any page URL — e.g. `/?vibe=1`. A
  "Tune Vibe" button appears bottom-right.
- **What you can tune:** every palette color (color pickers), the four type
  families, the Fraunces dials (WONK, SOFT, optical size, weight), and the
  handwritten note size + tilt.
- **Persistence:** tuning is saved in your browser (localStorage) and applies
  across all pages.
- **Share a look:** hit **Copy Link** — it copies a URL with the full look
  encoded in a `?t=...` param. Anyone opening that link sees the same colors
  and type instantly, no setup needed.
- **Lock it in permanently:** hit **Export CSS** — copy the `:root` block it
  generates and paste it over the one in `site.css` (bump the `?v=` on
  `site.css` in `base.html` so browsers pick it up).

Tuner files: `vibe-tuner.css` / `vibe-tuner.js` / `partials/vibe_tuner.html` —
all gated behind `?vibe=1` in `base.html`.

## Deployment

Push to `main` → Railway auto-deploys (GitHub source connected).
Procfile runs `migrate` + `collectstatic` before gunicorn starts.
