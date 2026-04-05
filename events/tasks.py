"""Background tasks for events."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

from events.models import Event
from registrations.models import Registration

logger = logging.getLogger("events")


@shared_task
def send_event_reminders() -> dict:
    """Send reminders for events that start in the next 24 hours."""

    now = timezone.now()
    horizon = now + timedelta(hours=24)

    registrations = Registration.objects.select_related("event", "user").filter(
        status="confirmed",
        event__start_date__gte=now,
        event__start_date__lte=horizon,
    )

    notified = 0
    for registration in registrations:
        if not registration.user.email:
            continue
        logger.info(
            "event_reminder_ready",
            extra={
                "registration_id": str(registration.id),
                "event_id": str(registration.event.id),
                "user_id": str(registration.user.id),
            },
        )
        notified += 1

    return {"status": "ok", "notified": notified}


@shared_task
def generate_event_report(event_id: str) -> dict:
    """Return simple event aggregate data for reporting workflows."""

    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        logger.warning("event_report_missing_event", extra={"event_id": str(event_id)})
        return {"status": "not_found", "event_id": str(event_id)}

    registrations = Registration.objects.filter(event=event)
    total_registrations = registrations.count()
    total_revenue = sum(reg.total_amount for reg in registrations)
    report = {
        "status": "ok",
        "event_id": str(event.id),
        "total_registrations": total_registrations,
        "total_revenue": float(total_revenue),
    }
    logger.info("event_report_generated", extra=report)
    return report
