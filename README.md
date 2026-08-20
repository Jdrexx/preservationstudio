# preservation.studio

Website for **Preservation Studio** — a custom framing program and preservation studio
based in Los Angeles, founded by Asher Cano.

Built with **Python / Django 6**. Deployed on **Railway**. Repo: `Jdrexx/preservationstudio`.

## Pages (launch version)

| Route | Page | Form |
|---|---|---|
| `/` | Home — hero, offerings, sponsor a seat | Waitlist (email) |
| `/intensive/` | Custom Framing Intensive — sessions, pricing | Full application |
| `/weekend/` | Custom Framing Weekend — cities, interest list | Name / email / city |
| `/sentimental-value/` | Sentimental Value series | Object story + photo upload |
| `/about/` | Bio, philosophy, FAQ | — |
| `/contact/` | Email, Instagram, inquiries | Sponsor / workshop / general message |

Every submission is stored in the database and reviewed in the Django admin
(admin is mounted at a secret path set by `DJANGO_ADMIN_URL` — unset = admin disabled).

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

## Deployment

Push to `main` → Railway auto-deploys (GitHub source connected).
Procfile runs `migrate` + `collectstatic` before gunicorn starts.
