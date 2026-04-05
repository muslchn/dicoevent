"""Celery app configuration for async tasks."""

from __future__ import annotations

import os
from importlib import import_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dicoevent_project.settings")

try:
    celery_module = import_module("celery")
except ModuleNotFoundError:  # pragma: no cover
    app = None
else:
    Celery = getattr(celery_module, "Celery")
    app = Celery("dicoevent_project")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
