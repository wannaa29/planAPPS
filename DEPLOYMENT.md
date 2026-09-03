# Deployment: local + wann-dev.my.id

The Django settings already allow both local development and the public host:

- Local: `http://127.0.0.1:8000` or `http://localhost:8000`
- Public: `https://wann-dev.my.id` (and `https://www.wann-dev.my.id`)

## Server checklist

1. Point an `A` DNS record for `wann-dev.my.id` (and optionally `www`) to the server IP.
2. Create a Python virtual environment and install `requirements.txt`.
3. Copy `.env.example` to `.env` (or export the same variables in the service manager). Set a unique `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, and production PostgreSQL/Redis credentials.
4. Run migrations and collect static assets:

   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. Start the web process with the included `Procfile` command:

   ```bash
   gunicorn workflow_planner.wsgi:application --bind 127.0.0.1:8000
   ```

6. Put Nginx, Caddy, or a managed reverse proxy in front of Gunicorn and enable TLS for `wann-dev.my.id`. Forward `X-Forwarded-Proto: https` so Django’s production security settings work correctly.
7. If Cloudflare proxying is enabled, purge the cache after a release (especially `/service-worker.js` and `/static/*`) so browsers receive the latest CSS and PWA cache version.

For local work, leave `DJANGO_DEBUG=1` and use SQLite. The local database and `.env` are intentionally ignored by Git; only migrations, source, templates, and static source assets should be committed.

After installation, Android users can long-press the WorkFlow Planner icon to access the Today, Tasks, and Calendar shortcuts. The compact `/widget/` page is designed for pinning as a second home-screen shortcut when a true native widget is required; native OS widgets require a platform-specific Android/iOS app and are outside standard PWA capabilities.

Schedule Flow keeps the reusable templates in the database and creates dated calendar entries from them. The service worker caches the offline page and the browser push handler is ready for a push provider; internal Django alerts continue to work online, while local task/note changes are queued offline and synced on reconnect.
