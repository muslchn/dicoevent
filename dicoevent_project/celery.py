"""Celery app configuration for async tasks."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dicoevent_project.settings")

app = Celery("dicoevent_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
