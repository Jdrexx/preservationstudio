# preservation.studio

Website for **Preservation Studio** — a custom framing program and preservation studio
based in Los Angeles, founded by Asher Cano.

Built with **Python / Django 6**. Deployed on **Railway**. Repo: `Jdrexx/preservationstudio`.

## Pages (launch version)

Nested page layout — parent pages hold the info, child pages hold the forms.

| Route                 | Page                                           | Nested                                             |
| --------------------- | ---------------------------------------------- | -------------------------------------------------- |
| `/`                   | Home — hero, offerings, sponsor a seat         | Waitlist form (inline)                             |
| `/intensive/`         | Custom Framing Intensive — sessions, pricing   | `/intensive/apply/` — full application             |
| `/weekend/`           | Custom Framing Weekend — cities, interest list | Interest form (inline)                             |
| `/sentimental-value/` | Sentimental Value series                       | `/sentimental-value/apply/` — object story + photo |
| `/about/`             | Bio, philosophy                                | `/about/faq/` — FAQ                                |
| `/contact/`           | Email, Instagram, message form                 | `/contact/sponsor/` — sponsored seat inquiry       |

Every submission is stored in the database and reviewed in the Django admin
(admin is mounted at a secret path set by `DJANGO_ADMIN_URL` — unset = admin disabled).

## Submission notifications (email + admin)

Every inquiry is **always** saved to the database and visible in the admin —
the email is an extra alert on top.

| Submission                    | Admin model                         | Email subject                            |
| ----------------------------- | ----------------------------------- | ---------------------------------------- |
| Home waitlist                 | `WaitlistEntry`                     | New waitlist signup                      |
| Weekend interest              | `WeekendInterest`                   | New Custom Framing Weekend interest      |
| Intensive application         | `IntensiveApplication`              | New Custom Framing Intensive application |
| Sentimental Value application | `SentimentalValueApplication`       | New Sentimental Value application        |
| Contact message               | `ContactMessage`                    | New contact message                      |
| Sponsor seat inquiry          | `ContactMessage` (kind=sponsorship) | New sponsored seat inquiry               |

To receive email alerts, set on Railway:

| Variable                | Example                                                    | Purpose                                                                    |
| ----------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| `DJANGO_NOTIFY_EMAIL`   | `alerts@yourdomain.com`                                    | Where summaries are sent. Empty/unset = no emails, submissions still saved |
| `DJANGO_EMAIL_HOST`     | `smtp.gmail.com` / `smtp.sendgrid.net` / `smtp.resend.com` | SMTP server of any provider                                                |
| `DJANGO_EMAIL_PORT`     | `587`                                                      | SMTP port (default 587)                                                    |
| `DJANGO_EMAIL_USER`     | your SMTP username                                         |                                                                            |
| `DJANGO_EMAIL_PASSWORD` | your SMTP password                                         |                                                                            |
| `DJANGO_EMAIL_USE_TLS`  | `1`                                                        | TLS on (default)                                                           |
| `DJANGO_FROM_EMAIL`     | `Preservation Studio <no-reply@...>`                       | From address (optional)                                                    |

Email sending is best-effort: if the mail server is unreachable the submission
still saves and the visitor still sees the thank-you page (failure is logged).

⚠️ **Do not put a period in an unquoted display name.** Django's SMTP backend
parses `From` on every send and rejects `preservation.studio <no-reply@…>`
(`period in 'phrase'`). Because sending is best-effort the failure is silent —
the client simply stops receiving alerts with nothing on screen to show for it.
Quote it (`"preservation.studio" <no-reply@…>`) or drop the period. The
`studio.E002` system check blocks the deploy if it is wrong.

This domain's mail is hosted on iCloud (MX `mx01/mx02.mail.icloud.com`), so the
branded sender needs no DNS changes:

```
DJANGO_NOTIFY_EMAIL=alerts@preservation.studio
DJANGO_EMAIL_HOST=smtp.mail.me.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USER=hello@preservation.studio
DJANGO_EMAIL_PASSWORD=<app-specific password from appleid.apple.com>
DJANGO_EMAIL_USE_TLS=1
DJANGO_FROM_EMAIL=Preservation Studio <no-reply@preservation.studio>
```

Verify a live configuration by sending a real submission and confirming the
email arrives — a passing test suite proves the code path, not the credentials.

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

| Variable               | Purpose                                                     |
| ---------------------- | ----------------------------------------------------------- |
| `DJANGO_SECRET_KEY`    | Production secret — required                                |
| `DJANGO_DEBUG`         | `0` in production                                           |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated, e.g. `preservation.studio,.up.railway.app` |
| `DJANGO_ADMIN_URL`     | Secret admin path, e.g. `studio-admin` → `/studio-admin/`   |
| `DATABASE_URL`         | Postgres connection string (Railway injects)                |

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

| Role                 | Font                    | Notes                                      |
| -------------------- | ----------------------- | ------------------------------------------ |
| Display (headlines)  | **Fraunces**            | Variable: optical size, weight, SOFT, WONK |
| Body                 | **Newsreader**          | Long-form reading                          |
| Labels / institution | **IBM Plex Mono**       | Nav, buttons, section numbers              |
| Handwritten notes    | **Kalam** (alt: Caveat) | Hero annotation accents                    |

**Vibe tuner library** — the `?vibe=1` tuner offers every family below as a
Display / Body / Mono / Notes pick (all self-hosted, latin-only woff2):

| Stack   | Families                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Display | Fraunces, Playfair Display, Libre Bodoni, Cormorant Garamond, Gloock, Italiana, Bricolage Grotesque, Georgia                 |
| Body    | Newsreader, Libre Caslon Text, Source Serif 4, Cormorant Garamond, Inter, Switzer, Space Grotesk, Archivo, Fraunces, Georgia |
| Mono    | IBM Plex Mono, JetBrains Mono, Space Mono, Courier New                                                                       |
| Notes   | Kalam, Caveat, Permanent Marker, Kaushan Script, Dancing Script, Pacifico, Satisfy, Yellowtail, Grand Hotel                  |

**Free stand-ins for the client's Creative Market picks** — picked off the
actual specimen sheets, not by name similarity (import now, swap for the
purchased woff2s later without touching the tuner):

| Creative Market font                 | What the specimen actually is                                        | Closest free match (in the tuner)                        |
| ------------------------------------ | -------------------------------------------------------------------- | -------------------------------------------------------- |
| **Promenade** — a calligraphic serif | Didone-grade contrast, sharp wedge serifs, ~10° italic               | **Libre Bodoni**, Playfair Display, Cormorant Garamond   |
| **Makking** — variable sans grotesk  | neo-grotesk: single-storey `a`, double-storey `g`, wide weight range | **Switzer**, Inter, Bricolage Grotesque, Archivo         |
| **Paloma** — hand-painted font       | flat-brush, letters **unjoined**, slight right slant, medium/bold    | **Permanent Marker**, Kaushan Script, Yellowtail, Caveat |

All five new files are free for commercial use and self-hosted like the rest:
Libre Bodoni / Permanent Marker / Kaushan Script are Google Fonts (OFL),
Switzer is Fontshare (ITF Free Font License).

> **Adding a purchased font (e.g. a Creative Market webfont):** drop the woff2
> into `studio/static/studio/fonts/`, add one `@font-face` per family in
> `fonts.css`, add an `<option>` in `partials/vibe_tuner.html` for its stack,
> and mirror it in the matching `STACKS` map in `js/vibe-tuner.js`. Bump the
> `?v=` on `vibe-tuner.js` so browsers reload it. Then update the
> `client-picks` look in the `PRESETS` array. `DesignLibraryTests` fails on
> whichever of those five steps you skipped.

**Palette** (Archive / research-library — from the client's own
`Hexcodes.txt` and the colours sampled off his newest mockups; token names
unchanged so the vibe tuner keeps working):

| Token           | Hex                    | Use                            |
| --------------- | ---------------------- | ------------------------------ |
| `--paper`       | `#F5F1EA` Cream        | Page background                |
| `--paper-deep`  | `#EAE3D4`              | Alternate section bands        |
| `--card`        | `#FFFFFF` White        | Catalogue cards, form panels   |
| `--ink`         | `#24140C` Licorice     | Text                           |
| `--ink-soft`    | `#5F5A41` Olive Night  | Labels, captions, card body    |
| `--rule`        | `#D5D5BC` Pearl        | Hairlines                      |
| `--rule-strong` | `#B3A189` Cinnamon     | Borders, rules                 |
| `--butter`      | `#FFDE8A` Honey        | Accent, marker highlights      |
| `--on-butter`   | `#24140C` Licorice     | Text on the accent             |
| `--blue`        | `#9EBEC6` Light Blue   | CTAs (the mockups' pill button) |
| `--plum`        | `#3D2D2E` Choc. Plum   | Hero band, footer, frames      |

`--on-butter` exists so a look can flip the accent to something light
(butter yellow, say) and set dark text on it without editing component CSS.
Every button/annotation that sits on the accent reads it instead of a
hard-coded cream — the Bold Red palette hard-coded cream, which turned into
cream-on-Honey (1.16:1) the moment the accent went light again.

**Type** is Asher's trio, each a self-hosted free stand-in for a paid
Creative Market font. Swapping in the purchased webfonts is a one-line change
per role in `:root`:

| Role      | Token      | Stand-in          | Client's pick |
| --------- | ---------- | ----------------- | ------------- |
| Titles    | `--script` | Permanent Marker  | Paloma        |
| Subheads  | `--display`| Libre Bodoni      | Promenade     |
| Paragraph | `--serif`  | Switzer           | Makking       |
| Labels    | `--mono`   | IBM Plex Mono     | —             |
| Notes     | `--hand`   | Kalam             | —             |

Design notes: uppercase editorial headlines (`.display-upper`), pill-shaped
buttons, split hero with a CSS "specimen card" standing in for photography,
two-column value band with flat SVG motifs, maroon "Meet the studio" band
with a polaroid collage, and the "Is this for you?" grid on the Intensive
page (recreated from the client's Canva mockup). All template component
styles live in the "BOLD RED editorial layer" section at the end of
`site.css`.

## Vibe tuner (?vibe=1)

A hidden design room for tuning the look live. Visitors never see it.

- **Open it:** append `?vibe=1` to any page URL — e.g. `/?vibe=1`. A
  "Tune Vibe" button appears bottom-right.
- **Looks (presets):** one-click recreations of what the client actually sent
  over. Each is a complete state — palette + all four stacks + the dials — so
  switching never leaves a stray value behind. Clicking one drops the same
  values into every picker below it, so you can keep tuning from there.
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

**The four looks** (source recorded in the panel note for each):

| Look                       | Recreates                                                                                                                                           |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bold Red — template        | The "Bold Red" Squarespace template (RowMarketCo, Etsy). Ships as the site default.                                                                 |
| Asher's Canva mockup       | Palette sampled live off Asher's Canva design — cream `#F5F1EA`, brick `#842B2C`, light orange `#EEDBBC`, greige `#D1C8B7`, navy `#182C59`.         |
| Archive / Research Library | The written brief: archive-library minimalism, warm neutral field, butter-yellow + light-blue pop. Amber accent, dark text on it via `--on-butter`. |
| Asher's picks (free)       | His three Creative Market fonts through the free stand-ins — Libre Bodoni / Switzer / Permanent Marker.                                             |

Tuner files: `vibe-tuner.css` / `vibe-tuner.js` / `partials/vibe_tuner.html` —
all gated behind `?vibe=1` in `base.html`.

## Deployment

Push to `main` → Railway auto-deploys (GitHub source connected).
Procfile runs `migrate` + `collectstatic` before gunicorn starts.
