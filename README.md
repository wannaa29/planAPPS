# WorkFlow Planner

A server-rendered Django MVP for coordinating tasks, shifts, projects, milestones, and deadlines.

## Run locally

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/register/` to create an account. New accounts receive a small demo workspace so the dashboard is useful immediately. SQLite is the local default; set `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` for PostgreSQL deployment.

For public deployment on `wann-dev.my.id`, see [DEPLOYMENT.md](DEPLOYMENT.md). Copy `.env.example` to a secret environment file; `.gitignore` keeps it, the local SQLite database, collected static files, media uploads, caches, logs, and IDE files out of the repository.

## Included MVP

- Authentication, registration, password reset entry point
- Dashboard with shifts, tasks, deadlines, milestones, projects, alerts, and notifications
- Task, project, milestone, and shift creation with server-side access scoping
- Week calendar and project timeline views
- Cross-midnight shift calculations
- Celery task seam for overdue detection and a `SchedulingService` abstraction for future smart planning
- Full CRUD actions with confirmation screens and permission checks
- PWA manifest, service worker, responsive navigation drawer, install prompt, and mobile-friendly animations
- Date/time validation prevents new or edited work from being scheduled in the past
- Compact `/widget/` snapshot and PWA shortcuts for Today, Tasks, and Calendar. Native OS widgets are not available to standard PWAs, but this page can be pinned as a home-screen shortcut.
- Saved shift templates are available at `/shift-templates/` and appear in the New shift form.
- Schedule Flow now creates calendar entries only by selecting a saved template; the legacy `/shifts/` route redirects to Calendar.
- Notes app with title and text body displayed as a responsive card grid.
- Notes cards open a read-only detail view at `/notes/<id>/`; editing is a separate action, and excerpts are capped at 30 words server-side.
- Offline page plus local task/note queue that syncs to `/sync/offline/` when the browser comes back online.
- Persistent dark mode toggle stored in the browser.
- Root dashboard acts as an app launcher for the separate Notes and Schedule Flow experiences.
