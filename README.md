# DicoEvent

DicoEvent is a Django REST API for event management. The current codebase provides:

- JWT-based authentication
- role-aware access control for users, organizers, admins, and superusers
- event, ticket, registration, and payment endpoints
- PostgreSQL-backed persistence
- API request/response logging middleware with rotating log files
- cache-backed read paths with namespace invalidation on write operations
- optional Celery-compatible async task hooks (sync fallback when Celery worker is absent)
- deterministic local seeding and Newman/Postman test execution

This README is intentionally limited to what is implemented in this repository today.

## Technology Stack

- Python 3.10+
- Django 4.2
- Django REST Framework
- Simple JWT
- PostgreSQL
- `python-decouple` for environment variables
- `django-filter`
- `django-redis` (optional Redis cache backend)
- Celery + Redis client packages (optional async worker backend)
- `python-json-logger` (installed dependency)
- Newman for Postman collection execution

Installed Python dependencies are defined in [requirements.txt](requirements.txt).

## Project Layout

```text
dicoevent/
├── api/
├── dicoevent_project/
├── events/
├── payments/
├── registrations/
├── tickets/
├── users/
├── docs/
├── [788] DicoEvent Versi 1 Postman/
├── [788] DicoEvent Versi 2 Postman/
├── create_initial_data.py
├── initialize_test_data.py
├── setup_test_data.py
├── test-suite.sh
├── report-tests.sh
├── manage.py
├── Makefile
├── Pipfile
├── requirements.txt
└── scripts/
    └── run_newman.py
```

Notes:

- The active Django settings module is [dicoevent_project/settings.py](dicoevent_project/settings.py).
- There is no root-level `docker-compose.yml` in this repository.
- Postman assets are kept under [[788] DicoEvent Versi 1 Postman]([788]%20DicoEvent%20Versi%201%20Postman) and [[788] DicoEvent Versi 2 Postman]([788]%20DicoEvent%20Versi%202%20Postman).

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 13 or newer
- `pip` or `pipenv`
- Node.js with Newman installed if you want to run the Postman collection

Optional Newman installation (global):

```bash
npm install -g newman
```

## Environment Configuration

Copy the template and edit it:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The Django application reads these variables:

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

Optional variables (default values are already handled in settings):

```env
# Cache backend
CACHE_BACKEND=locmem
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=1

# Celery backend
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email sender identity for async notifications
DEFAULT_FROM_EMAIL=noreply@dicoevent.local
```

Local Newman helpers additionally use:

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

Then verify access and run migrations:

```bash
PGPASSWORD=your_secure_password_here psql -h localhost -U dicoevent_user -d dicoevent_production -c "SELECT version();"
python manage.py makemigrations
python manage.py migrate
```

You can also use the helper target:

```bash
make db-init
make migrate
```

## Local Development

Install dependencies with either `pipenv` or `pip`:

```bash
pipenv install --dev
pipenv shell
```

or:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you plan to run [test-suite.sh](test-suite.sh), keep the virtual environment at `venv/` because that script currently resolves Python from `venv/bin/python`.

Run the server:

```bash
python manage.py runserver 0.0.0.0:8000
```

or:

```bash
make run
```

## Quick Start (Without Docker)

This is the recommended local flow for this repository:

```bash
# 1) activate local virtualenv
source venv/bin/activate

# 2) apply schema
python manage.py migrate

# 3) load deterministic baseline data
python initialize_test_data.py

# 4) run API
python manage.py runserver 0.0.0.0:8000
```

In another terminal, run Newman against Version 2 assets:

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent versi 2.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

Quick API readiness check (any HTTP response code confirms process is reachable):

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
```

Expected Newman V2 baseline result in this repository state is:

- 78 requests
- 197 assertions
- 0 failed assertions

## Seed Scripts

This repository contains three seed helpers:

- [create_initial_data.py](create_initial_data.py): baseline local users
- [initialize_test_data.py](initialize_test_data.py): deterministic dataset for Newman collection runs
- [setup_test_data.py](setup_test_data.py): broader sample dataset for manual/API testing

These scripts are idempotent and can be run repeatedly without duplicating their seeded records.

## Testing

Run the Django test suite:

```bash
python manage.py test --verbosity=2
```

or:

```bash
make djtest
```

If `pytest` is installed in your active environment, this also works:

```bash
pytest
```

Note: `pytest` is optional. `python manage.py test` is the canonical test command in this repository.

Run the full local API validation workflow (database reset, seed, server startup, Newman run, summary):

```bash
./test-suite.sh
```

`./test-suite.sh` expects both [.env](.env) and a virtual environment at `venv/`.

Generate a standalone summary from the latest Newman JSON report:

```bash
./report-tests.sh
```

## Newman / Postman

Preferred: run the Python wrapper directly with explicit collection and environment paths.

Version 1:

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 1 Postman/[788] DicoEvent versi 1.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 1 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

Version 2:

```bash
python scripts/run_newman.py \
    --collection "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent versi 2.postman_collection.json" \
    --environment "./[788] DicoEvent Versi 2 Postman/[788] DicoEvent.postman_environment.json" \
    --timeout-request 60000
```

The direct wrapper expects the Django server to already be running.

You can also run the Make target:

```bash
make postman
```

What `make postman` does:

1. flushes the database
2. runs [initialize_test_data.py](initialize_test_data.py)
3. executes [scripts/run_newman.py](scripts/run_newman.py)

Unlike [test-suite.sh](test-suite.sh), `make postman` does not start Django for you. Start the API server first, then run the target.

The Python Newman wrapper uses a temporary copy of the checked-in Postman collection so `{{host}}` and `{{port}}` placeholders inside embedded `pm.sendRequest(...)` scripts resolve correctly, and so the user-update request stays aligned with the collection's `{{newUsername}}` assertion, without modifying the original Postman files.

Best-practice rule for this repository: do not edit files inside [Postman Version 1 folder]([788]%20DicoEvent%20Versi%201%20Postman) or [Postman Version 2 folder]([788]%20DicoEvent%20Versi%202%20Postman) to fix runtime variable resolution.

For the all-in-one local run, [test-suite.sh](test-suite.sh) uses the Node wrapper [run-newman-fixed.js](run-newman-fixed.js), which starts Django, runs Newman, and prints the parsed summary. Because it also references legacy `DicoEvent_Versi_1_Postman/...` paths today, verify/update those paths before relying on it in this workspace.

## Known Local Caveats

- [scripts/run_newman.py](scripts/run_newman.py), [Makefile](Makefile), [test-suite.sh](test-suite.sh), and [run-newman-fixed.js](run-newman-fixed.js) still contain legacy default paths (`DicoEvent_Versi_1_Postman/...`).
- The checked-in folders in this workspace are [[788] DicoEvent Versi 1 Postman]([788]%20DicoEvent%20Versi%201%20Postman) and [[788] DicoEvent Versi 2 Postman]([788]%20DicoEvent%20Versi%202%20Postman).
- For reliable local execution without editing collection files, always pass explicit `--collection` and `--environment` values to [scripts/run_newman.py](scripts/run_newman.py), as shown above.
- [scripts](scripts) currently contains only [run_newman.py](scripts/run_newman.py), so Makefile targets `readme`, `doc-links`, and `docs` are present but will fail until their helper scripts are added.

## Useful Make Targets

```bash
make env
make venv
make db-init
make migrate
make createsuper
make run
make djtest
make postman
```

The source for these commands is [Makefile](Makefile). Additional targets in the Makefile may reference helper scripts that are not currently present in [scripts](scripts).

## Documentation

Additional project documentation is available under [docs](docs).

## Current Scope

This README documents only components that are either active by default or already wired with optional runtime backends in code. In particular:

- Caching and structured logging are active in current settings.
- Celery configuration and task hooks exist, but a worker and broker are optional for local API execution.
- Docker Compose orchestration, Sentry, Stripe, and alternate Django settings modules are not part of the current local workflow described here.
