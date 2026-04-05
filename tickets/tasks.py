"""Background tasks for ticket operations."""

from __future__ import annotations

import logging

from api.celery_compat import shared_task
from registrations.models import Registration
from tickets.models import Ticket

logger = logging.getLogger("tickets")


@shared_task
def generate_ticket_qr_codes(registration_id: str) -> dict:
    """Placeholder async workflow for ticket artifact generation."""

    try:
        registration = Registration.objects.get(pk=registration_id)
    except Registration.DoesNotExist:
        logger.warning(
            "ticket_artifact_missing_registration",
            extra={"registration_id": str(registration_id)},
        )
        return {"status": "not_found", "registration_id": str(registration_id)}

    ticket_count = Ticket.objects.filter(ticket_type=registration.ticket_type).count()
    logger.info(
        "ticket_artifact_generated",
        extra={
            "registration_id": str(registration.id),
            "ticket_type_id": str(registration.ticket_type.id),
            "existing_ticket_count": ticket_count,
        },
    )
    return {
        "status": "ok",
        "registration_id": str(registration.id),
        "existing_ticket_count": ticket_count,
    }
