# Deployment: local + wanand.my.id

The Django settings already allow both local development and the public host:

- Local: `http://127.0.0.1:8000` or `http://localhost:8000`
- Public: `https://wanand.my.id` (and `https://www.wanand.my.id`)

## Server checklist

1. Point an `A` DNS record for `wanand.my.id` (and optionally `www`) to the server IP.
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

6. Put Nginx, Caddy, or a managed reverse proxy in front of Gunicorn and enable TLS for `wanand.my.id`. Forward `X-Forwarded-Proto: https` so Django’s production security settings work correctly.

For local work, leave `DJANGO_DEBUG=1` and use SQLite. The local database and `.env` are intentionally ignored by Git; only migrations, source, templates, and static source assets should be committed.
