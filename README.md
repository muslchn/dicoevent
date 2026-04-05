# DicoEvent

DicoEvent is a Django REST API for event management. The current codebase provides:

- JWT-based authentication
- role-aware access control for users, organizers, admins, and superusers
- event, ticket, registration, and payment endpoints
- PostgreSQL-backed persistence
- media file storage for event poster images
- API request/response logging middleware with rotating log files
- cache-backed read paths with namespace invalidation on write operations
- Celery async task hooks (Redis broker required; tasks run in the background)
- deterministic local seeding and Newman/Postman test execution

This README documents only what is implemented and active in this repository today.

## Technology Stack

| Component | Detail |
| --- | --- |
| Python | 3.10 or newer |
| Django | 4.2 |
| Django REST Framework | API layer |
| Simple JWT | Bearer token authentication |
| PostgreSQL | Primary database |
| `python-decouple` | Environment variable loading |
| `django-filter` | Query filtering |
| `redis` | Redis client library (cache backend + Celery broker) |
| Celery + Redis | Optional async task worker/broker |
| `python-json-logger` | Structured log formatting |
| Newman | Postman collection runner |

Installed Python dependencies are defined in [requirements.txt](requirements.txt).

## Project Layout

```text
dicoevent/
├── api/                              # Shared middleware, cache utils, celery compat
├── dicoevent_project/                # Django project settings, urls, wsgi, asgi, celery
├── events/                           # Events app (models, views, serializers, tasks)
├── payments/                         # Payments app
├── registrations/                    # Registrations app
├── tickets/                          # Tickets and ticket types app
├── users/                            # Custom user model, auth, group management
├── docs/                             # Extended project documentation
├── media/                            # Uploaded media files (event posters)
├── test_uploads/                     # Fixture images for Newman file upload tests
├── logs/                             # Rotating log files (generated at runtime)
├── [788] DicoEvent Versi 1 Postman/  # Version 1 Postman collection and environment
├── [788] DicoEvent Versi 2 Postman/  # Version 2 Postman collection and environment
├── create_initial_data.py
├── initialize_test_data.py
├── setup_test_data.py
├── run-newman-fixed.js               # Node.js Newman wrapper (resolves template vars)
├── test-suite.sh
├── report-tests.sh
├── manage.py
├── Makefile
├── Pipfile
├── requirements.txt
└── scripts/
    └── run_newman.py                 # Python Newman wrapper (portable, preferred)
```

Notes:

- The active Django settings module is [dicoevent_project/settings.py](dicoevent_project/settings.py).
- Media uploads are stored under `media/` at the project root and served at `/media/` in development.
- There is no root-level `docker-compose.yml` in this repository.
- Postman assets are kept under [[788] DicoEvent Versi 1 Postman]([788]%20DicoEvent%20Versi%201%20Postman) and [[788] DicoEvent Versi 2 Postman]([788]%20DicoEvent%20Versi%202%20Postman). Do not edit these files.

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 13 or newer
- **Redis 6 or newer** (required — used for both the cache layer and the Celery task broker)
- `pipenv` (recommended) or `pip`
- Node.js with Newman installed globally to run the Postman collection

Install Newman globally:

```bash
npm install -g newman
```

## User Roles

The custom `User` model uses a four-level role hierarchy. Each role inherits the permissions of the roles below it.

| Role | Description | Key permissions |
| --- | --- | --- |
| `user` | Regular attendee | Register for events, view own registrations and payments |
| `organizer` | Event creator | All of the above, plus create/edit/publish/cancel own events, manage ticket types |
| `admin` | Administrator | All organizer permissions plus manage all users and registrations, update payment status |
| `superuser` | Platform superuser | All admin permissions plus assign roles, manage groups, full platform access |

Role is stored in the `role` field of the `User` model. Django `is_staff` / `is_superuser` flags are also set for `admin` and `superuser` accounts respectively.

## API Endpoints

All endpoints are prefixed with `/api/`. Authentication uses a `Bearer <access_token>` header.

### Authentication

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/api/register/` | None | Register a new user account |
| `POST` | `/api/login/` | None | Obtain access + refresh token pair |
| `POST` | `/api/token/` | None | Obtain or refresh token (unified endpoint) |
| `POST` | `/api/token/refresh/` | None | Refresh an access token |

### Users

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/users/` | Admin/Superuser | List all users |
| `POST` | `/api/users/` | Admin/Superuser | Create a user |
| `GET` | `/api/users/me/` | Authenticated | Get own profile |
| `GET` | `/api/users/<id>/` | Admin/Superuser | Get a specific user |
| `PUT/PATCH` | `/api/users/<id>/` | Authenticated (own) or Admin | Update user |
| `DELETE` | `/api/users/<id>/` | Admin/Superuser | Delete user |
| `PATCH` | `/api/users/<id>/role/` | Admin/Superuser | Update user role |
| `POST` | `/api/assign-roles/` | Superuser | Assign user to a group |

### Groups

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/groups/` | Authenticated | List groups |
| `POST` | `/api/groups/` | Admin/Superuser | Create group |
| `GET` | `/api/groups/<id>/` | Authenticated | Get group detail |
| `PUT/PATCH` | `/api/groups/<id>/` | Admin/Superuser | Update group |
| `DELETE` | `/api/groups/<id>/` | Admin/Superuser | Delete group |

### Events

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/events/` | None / Authenticated | List events |
| `POST` | `/api/events/` | Organizer/Admin | Create event |
| `GET` | `/api/events/<id>/` | None / Authenticated | Get event detail |
| `PUT/PATCH` | `/api/events/<id>/` | Organizer (own) / Admin | Update event |
| `DELETE` | `/api/events/<id>/` | Organizer (own) / Admin | Delete event |
| `POST` | `/api/events/<id>/publish/` | Organizer (own) / Admin | Publish event |
| `POST` | `/api/events/<id>/cancel/` | Organizer (own) / Admin | Cancel event |
| `GET` | `/api/events/upcoming/` | None | Upcoming published events |
| `GET` | `/api/events/my-events/` | Organizer | Own events |
| `POST` | `/api/events/upload/` | Organizer/Admin | Upload event poster image |
| `GET` | `/api/events/<id>/poster/` | Authenticated | Get event poster metadata |

### Tickets

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/tickets/ticket-types/` | Authenticated | List ticket types |
| `POST` | `/api/tickets/ticket-types/` | Organizer/Admin | Create ticket type |
| `GET` | `/api/tickets/ticket-types/<id>/` | Authenticated | Get ticket type detail |
| `PUT/PATCH` | `/api/tickets/ticket-types/<id>/` | Organizer (own) / Admin | Update ticket type |
| `DELETE` | `/api/tickets/ticket-types/<id>/` | Organizer (own) / Admin | Delete ticket type |
| `GET` | `/api/tickets/events/<event_id>/ticket-types/` | Authenticated | Ticket types for an event |
| `POST` | `/api/tickets/ticket-types/<id>/generate/` | Organizer/Admin | Generate individual ticket records |
| `GET` | `/api/tickets/` | Authenticated | List tickets |
| `GET` | `/api/tickets/<id>/` | Authenticated | Get ticket detail |
| `GET` | `/api/tickets/validate/<code>/` | Organizer/Admin | Validate a ticket code |
| `POST` | `/api/tickets/use/<code>/` | Organizer/Admin | Mark a ticket as used |

### Registrations

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/registrations/` | Authenticated | List registrations |
| `POST` | `/api/registrations/` | Authenticated | Create a registration |
| `GET` | `/api/registrations/<id>/` | Authenticated (own) / Admin | Get registration detail |
| `PUT/PATCH` | `/api/registrations/<id>/` | Admin | Update registration |
| `DELETE` | `/api/registrations/<id>/` | Admin | Delete registration |
| `GET` | `/api/registrations/my/` | Authenticated | Own registrations |
| `GET` | `/api/registrations/events/<event_id>/registrations/` | Organizer/Admin | Registrations for an event |
| `PATCH` | `/api/registrations/<id>/status/` | Admin | Update registration status |
| `POST` | `/api/registrations/<id>/cancel/` | Authenticated (own) / Admin | Cancel registration |

### Payments

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/payments/` | Authenticated | List payments |
| `POST` | `/api/payments/` | Authenticated | Create payment record |
| `GET` | `/api/payments/<id>/` | Authenticated (own) / Admin | Get payment detail |
| `PUT/PATCH` | `/api/payments/<id>/` | Admin | Update payment |
| `DELETE` | `/api/payments/<id>/` | Admin | Delete payment |
| `GET` | `/api/payments/my/` | Authenticated | Own payments |
| `POST` | `/api/payments/initiate/` | Authenticated | Initiate payment for a registration |
| `PATCH` | `/api/payments/<id>/status/` | Admin | Update payment status |
| `POST` | `/api/payments/<id>/refund/` | Admin | Refund a payment |

### Async Tasks

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/tasks/<task_id>/status/` | Authenticated | Poll async task status |

## Environment Configuration

Copy the template and fill in the required values:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Required variables:

```env
DATABASE_NAME=dicoevent_production
DATABASE_USER=dicoevent_user
DATABASE_PASSWORD=your_secure_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432

SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

JWT_ACCESS_TOKEN_LIFETIME_HOURS=3
```

Optional variables (defaults are handled in [settings.py](dicoevent_project/settings.py)):

```env
# Redis — required for both the cache layer and the Celery broker.
# Ensure a Redis server is running before starting the application.
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=1

# Celery async task broker (uses the same Redis instance by default)
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email sender identity for async notifications
DEFAULT_FROM_EMAIL=noreply@dicoevent.local
```

Newman helper variables:

```env
POSTMAN_HOST=localhost
POSTMAN_PORT=8000
NEW_USERNAME=DicodingIndonesia
```

The source template is [.env.example](.env.example).

## Database Setup

Create the local PostgreSQL database and user:

```sql
CREATE DATABASE dicoevent_production;
CREATE USER dicoevent_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE dicoevent_production TO dicoevent_user;
ALTER USER dicoevent_user CREATEDB;
```

Verify access and run migrations:

```bash
PGPASSWORD=your_secure_password_here psql -h localhost -U dicoevent_user -d dicoevent_production -c "SELECT version();"
python manage.py makemigrations
python manage.py migrate
```

Or use the Makefile helpers:

```bash
make db-init
make migrate
```

## Local Development

Install dependencies using `pipenv` (recommended):

```bash
pipenv install --dev
pipenv shell
```

Or with a plain virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Note:** [test-suite.sh](test-suite.sh) expects the virtual environment at `venv/` because it resolves Python from `venv/bin/python`.

Run the development server:

```bash
python manage.py runserver 0.0.0.0:8000
# or
make run
```

## Quick Start (Without Docker)

The recommended local flow for this repository:

```bash
# 1) Install dependencies and activate the environment
pipenv install --dev
pipenv shell

# 2) Configure environment
cp .env.example .env
# Edit .env with your database credentials and a generated SECRET_KEY

# 3) Apply database schema
python manage.py migrate

# 4) Seed data required by the Postman V2 collection
python setup_test_data.py

# 5) Start the API server
python manage.py runserver 0.0.0.0:8000
```

In a second terminal, run Newman against the Version 2 collection:

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent versi 2.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

Check API reachability:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/events/
```

Expected Newman V2 result:

- 78 requests, 0 failed
- 197 assertions, 0 failed

## Seed Scripts

| Script | Purpose |
| --- | --- |
| [create_initial_data.py](create_initial_data.py) | Minimal baseline users for manual testing |
| [initialize_test_data.py](initialize_test_data.py) | Full deterministic dataset (used by `make postman`) |
| [setup_test_data.py](setup_test_data.py) | Extended dataset that includes the `Aras` and `dicoding` accounts required by the Postman V2 environment variables |

All three scripts are idempotent — running them multiple times will not create duplicate records.

For the Postman V2 collection to pass, **`setup_test_data.py` must be run** before executing Newman. The collection's environment file sets `usernameSuperUser=Aras` and `username=dicoding`; these accounts are created by `setup_test_data.py`.

## Testing

Run the Django unit test suite:

```bash
python manage.py test --verbosity=2
# or
make djtest
```

If `pytest` is installed:

```bash
pytest
```

Run the full local API validation workflow (database reset, seed, server, Newman, summary):

```bash
./test-suite.sh
```

`./test-suite.sh` expects [.env](.env) and a virtual environment at `venv/`.

Generate a summary from the latest Newman JSON report:

```bash
./report-tests.sh
```

## Newman / Postman

> **Rule:** Do not edit files inside [[788] DicoEvent Versi 1 Postman]([788]%20DicoEvent%20Versi%201%20Postman) or [[788] DicoEvent Versi 2 Postman]([788]%20DicoEvent%20Versi%202%20Postman) to work around runtime issues.

### Recommended: Python wrapper (`scripts/run_newman.py`)

This is the portable method. It writes a temporary patched copy of the collection before passing it to Newman, resolving `{{host}}`/`{{port}}` backtick template literals in `pm.sendRequest()` calls and remapping the hardcoded `/home/aras/Downloads/` file-upload paths to the tracked [test_uploads/](test_uploads) directory.

**Version 2 (required for final submission):**

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent versi 2.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

**Version 1:**

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 1 Postman/[788] DicoEvent versi 1.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 1 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

The script requires the Django server to be running before it is called.

### Alternative: Node.js wrapper (`run-newman-fixed.js`)

[run-newman-fixed.js](run-newman-fixed.js) applies the same template-variable patching but does **not** remap the hardcoded `/home/aras/Downloads/` upload paths. Use this wrapper only if the upload fixture files are present at that path on your machine.

```bash
node run-newman-fixed.js \
    "[788] DicoEvent Versi 2 Postman/[788] DicoEvent versi 2.postman_collection.json" \
    "[788] DicoEvent Versi 2 Postman/[788] DicoEvent.postman_environment.json" \
    localhost 8000
```

### Make target

```bash
make postman
```

`make postman` flushes the database, runs [initialize_test_data.py](initialize_test_data.py), then calls [scripts/run_newman.py](scripts/run_newman.py). It does **not** reseed with `setup_test_data.py`, so the Postman V2 environment accounts (`Aras`, `dicoding`) will be absent. Run `setup_test_data.py` manually before using this target with the V2 collection.

### How the wrappers work

The V2 Postman collection contains `pm.sendRequest(...)` calls that embed `{{host}}` and `{{port}}` inside JavaScript backtick template literals. Newman cannot expand those variables inside script strings, causing a `RangeError: Port should be >= 0 and < 65536` error. Both wrappers work around this by creating a temporary in-memory copy of the collection with the variable references replaced by literal values before Newman loads the file.

## Fixture Files for Upload Tests

The Postman V2 collection includes tests that upload image files. The collection JSON hardcodes the path `/home/aras/Downloads/`. The Python wrapper ([scripts/run_newman.py](scripts/run_newman.py)) automatically remaps this to [test_uploads/](test_uploads), which is version-controlled and contains:

| File | Size | Purpose |
| --- | --- | --- |
| `test_uploads/6298845955545483427.jpg` | ~1 KB | Valid small poster image |
| `test_uploads/picture-large.jpg` | ~550 KB | Oversized image (tests the file size validation error path) |

If you use [run-newman-fixed.js](run-newman-fixed.js) instead, create `/home/aras/Downloads/` and copy both files there.

## Known Caveats

- The default collection and environment paths hard-coded in [run-newman-fixed.js](run-newman-fixed.js) and [scripts/run_newman.py](scripts/run_newman.py) point to Version 1 assets. Always pass explicit `--collection` and `--environment` arguments when targeting Version 2, as shown in the examples above.
- [scripts](scripts) currently contains only [run_newman.py](scripts/run_newman.py). The Makefile targets `readme`, `doc-links`, and `docs` reference helper scripts (`validate_readme.py`, `check_doc_links.py`) that are not present yet; those targets will fail until the scripts are added.
- Celery async tasks require Redis as the broker. Start Redis before running the API server or the Celery worker. All task files import `shared_task` directly from `celery`.
- The `media/` directory at the project root stores uploaded event poster images. It is tracked in version control via a `.gitkeep` placeholder. In production, configure a persistent storage backend instead of the local filesystem.

## Useful Make Targets

| Target | Action |
| --- | --- |
| `make env` | Copy `.env.example` to `.env` |
| `make venv` | Install dependencies and open `pipenv shell` |
| `make db-init` | Create PostgreSQL database and user |
| `make migrate` | Run `makemigrations` + `migrate` |
| `make createsuper` | Interactive superuser creation |
| `make run` | Start development server on `0.0.0.0:8000` |
| `make djtest` | Run Django unit tests |
| `make postman` | Flush DB, seed, and run Newman V1 (see note above for V2) |
| `make all` | `migrate` + `djtest` + `postman` |

Full command reference: [Makefile](Makefile).

## Documentation

Additional project documentation is available under [docs](docs):

- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) — detailed endpoint reference
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design overview
- [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) — production deployment notes
- [SECURITY.md](docs/SECURITY.md) — security considerations
- [TESTING.md](docs/TESTING.md) — testing strategy
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common issues and solutions

## Current Scope

This README documents only components that are either active by default or already wired in code:

- Caching uses Django’s built-in `RedisCache` backend only (`django.core.cache.backends.redis.RedisCache`) — a running Redis server is required.
- Celery is configured and all async tasks use `@shared_task` from the `celery` package directly. A Celery worker process is required for background task execution.
- Structured logging is active for all app modules.
- Docker Compose orchestration, Sentry, Stripe, and alternate Django settings modules are not part of the current local workflow described here.
