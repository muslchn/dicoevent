"""Background tasks for payments."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from api.celery_compat import shared_task
from payments.models import Payment

logger = logging.getLogger("payments")


@shared_task
def send_payment_confirmation_email(payment_id: str) -> dict:
    """Send confirmation email after successful payment."""

    try:
        payment = Payment.objects.select_related("user", "registration__event").get(
            pk=payment_id
        )
    except Payment.DoesNotExist:
        logger.warning(
            "payment_confirmation_missing", extra={"payment_id": str(payment_id)}
        )
        return {"status": "not_found", "payment_id": str(payment_id)}

    user_email = payment.user.email
    if not user_email:
        logger.info(
            "payment_confirmation_skipped_no_email",
            extra={"payment_id": str(payment.id)},
        )
        return {
            "status": "skipped",
            "reason": "no_email",
            "payment_id": str(payment.id),
        }

    subject = f"Payment Confirmed: {payment.registration.event.title}"
    body = (
        f"Hi {payment.user.username},\n\n"
        f"Your payment for {payment.registration.event.title} has been confirmed.\n"
        f"Amount: {payment.amount} {payment.currency}\n"
        f"Transaction ID: {payment.transaction_id or '-'}\n"
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True,
    )

    logger.info("payment_confirmation_sent", extra={"payment_id": str(payment.id)})
    return {"status": "ok", "payment_id": str(payment.id)}
