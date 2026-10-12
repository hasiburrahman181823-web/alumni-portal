# Alumni Portal (Django 5 + DRF + Tailwind)

## Quick start
```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # optional; defaults work for development
python manage.py migrate
python manage.py createsuperuser    # becomes role "Admin" automatically
python manage.py test               # 12 tests
python manage.py runserver
```
Open http://127.0.0.1:8000/ (site) · /admin/ (Django admin) · /api/ (browsable API)

## Roles
| Role    | Jobs                          | Events              | Users            |
|---------|-------------------------------|---------------------|------------------|
| General | post; edit/delete own         | read                | edit own profile |
| Staff   | + edit/delete anyone's        | create/edit/delete  | -                |
| Admin   | same as Staff                 | same as Staff       | + change roles at /accounts/manage/users/ |

Self-registration always creates a *General* user. Only an Admin can promote someone.

## REST API (token auth)
| Method | URL | Notes |
|---|---|---|
| POST | /api/auth/register/ | returns `{user, token}` |
| POST | /api/auth/token/ | `username` (or email) + `password` -> `{token}` |
| GET/PATCH | /api/me/ | own account + profile |
| PUT | /api/me/avatar/ | multipart, field `avatar` |
| GET/POST/PUT/PATCH/DELETE | /api/jobs/ | `?search= &job_type= &location= &ordering= &page=` |
| GET/POST/PUT/PATCH/DELETE | /api/events/ | `?when=upcoming\|past &search=` (writes: Staff/Admin) |
| GET | /api/alumni/ | `?search= &graduation_year= &department=` |

Send `Authorization: Token <key>` on every request.
```bash
curl -X POST localhost:8000/api/auth/token/ -d "username=admin&password=..."
curl localhost:8000/api/jobs/?search=django -H "Authorization: Token <key>"
```

## Going to production
1. `DJANGO_DEBUG=False`, a long random `DJANGO_SECRET_KEY`, real `DJANGO_ALLOWED_HOSTS`.
2. PostgreSQL: set `DB_ENGINE=postgres` and the `DB_*` variables.
3. `python manage.py collectstatic --noinput`, then run `gunicorn config.wsgi`.
4. Serve `/media/` (uploads) with nginx or move to S3 (django-storages); Django doesn't serve it when DEBUG is off.
5. Tailwind: the templates use the Play CDN for zero-setup development. For production, install the
   Tailwind CLI, point `content` at `./templates/**/*.html` and `./**/forms.py`, build to `static/css/tailwind.css`,
   and replace the CDN `<script>` in `templates/base.html` with a `<link>`.
