# DicoEvent

DicoEvent is a Django REST API for event management. The current codebase provides:

- JWT-based authentication
- role-aware access control for users, organizers, admins, and superusers
- event, ticket, registration, and payment endpoints
- PostgreSQL-backed persistence
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
├── DicoEvent_Versi_1_Postman/
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
- The Postman collection is kept under [DicoEvent_Versi_1_Postman](DicoEvent_Versi_1_Postman).

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 13 or newer
- `pip` or `pipenv`
- Node.js with Newman installed if you want to run the Postman collection

## Environment Configuration

Copy the template and edit it:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The current application reads these variables:

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
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server:

```bash
python manage.py runserver 0.0.0.0:8000
```

or:

```bash
make run
```

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

Run the full local API validation workflow (database reset, seed, server startup, Newman run, summary):

```bash
./test-suite.sh
```

Generate a standalone summary from the latest Newman JSON report:

```bash
./report-tests.sh
```

## Newman / Postman

Run the collection through the Make target:

```bash
make postman
```

What `make postman` does:

1. flushes the database
2. runs [initialize_test_data.py](initialize_test_data.py)
3. executes [scripts/run_newman.py](scripts/run_newman.py)

The Newman wrapper uses a temporary copy of the checked-in Postman collection so `{{host}}` and `{{port}}` placeholders inside embedded `pm.sendRequest(...)` scripts resolve correctly without modifying the original Postman files.

Best-practice rule for this repository: do not edit files inside [DicoEvent_Versi_1_Postman](DicoEvent_Versi_1_Postman) to fix runtime variable resolution.

You can also run the wrapper directly:

```bash
python scripts/run_newman.py --timeout-request 60000
```

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

The source for these commands is [Makefile](Makefile).

## Documentation

Additional project documentation is available under [docs](docs).

## Current Scope

This README does not document unsupported or unconfigured components such as Redis, Celery, Sentry, Stripe, docker-compose orchestration, or alternate Django settings modules, because they are not wired into the current repository state.
