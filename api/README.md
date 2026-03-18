# Livininbintaro

Unified property marketplace, CRM dashboard, and WhatsApp workflow for Ocha.

**Updated:** 2026-03-14  
**Current Repo Version:** `v2.1`

---

## Current State

This repository now contains the first implemented version of the V2 plan:

- Unified FastAPI backend under `/api/*`
- Vue 3 + Vite frontend in `frontend/`
- PWA setup with manifest, service worker, and install icons
- Public property browsing views
- Agent dashboard, lead Kanban, lead detail, WhatsApp, content, and listings management views

The old dual-app architecture is still relevant operationally in production, but this repo now holds the code path for the consolidated direction.

---

## Repo Structure

```text
/root/livininbintaro.my.id
├── app/                         # Unified FastAPI backend
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── presenters.py
│   └── routers/
│       ├── auth.py
│       ├── public.py
│       ├── listings.py
│       ├── leads.py
│       ├── wa.py
│       ├── dashboard.py
│       ├── content.py
│       ├── users.py
│       └── webhook.py
├── frontend/                    # Vue 3 + Vite + Pinia + PWA app
├── docs/
│   ├── README.md
│   ├── v2.0/                    # Original planning docs
│   └── v2.1/                    # Current implementation docs
├── sync_listings.py
├── sync_images.py
├── follow_up_cron.py
└── follow_up_reminder_cron.py
```

---

## API Surface

### Public

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/public/listings`
- `GET /api/public/listings/search`
- `GET /api/public/listings/{id}`
- `GET /api/public/districts`
- `GET /api/public/stats`

### Agent

- `GET /api/listings/`
- `PUT /api/listings/{id}`
- `POST /api/listings/sync`
- `GET /api/leads/`
- `GET /api/leads/{id}`
- `PUT /api/leads/{id}`
- `POST /api/leads/{id}/score`
- `GET /api/wa/messages/{lead_id}`
- `POST /api/wa/send`
- `GET /api/dashboard/stats`
- `GET /api/content/`

---

## Frontend

### Public Views

- `/`
- `/search`
- `/property/:id`
- `/login`

### Agent Views

- `/dashboard`
- `/leads`
- `/leads/:id`
- `/content`
- `/manage/listings`

---

## Docs

Read the latest implementation docs first:

1. `docs/README.md`
2. `docs/v2.1/00-OVERVIEW.md`
3. `docs/v2.1/01-IMPLEMENTATION-STATUS.md`
4. `docs/v2.1/02-VERIFICATION.md`

Use `docs/v2.0/` for the original planning baseline.

---

## Verification Completed

```bash
python3 -m compileall app
cd frontend && npm install
cd frontend && npm run build
```

The frontend production build currently passes.  
A live DB-backed backend smoke test is still the next verification step.

---

## Git Remote

`origin` is already set to:

```text
git@github.com-livinin:embohpokoke/livininbintaro.git
```

That keeps this workspace aligned with the GitHub repo for future pull/push sync.
