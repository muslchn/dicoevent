"""Integration tests for payment API flows and permissions."""

from datetime import timedelta
from typing import Any, cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from events.models import Event
from payments.models import Payment
from registrations.models import Registration
from tickets.models import TicketType
from users.models import User


class PaymentApiTests(TestCase):
    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()
        self.admin_user = User.objects.create_user(
            username="paymentadmin",
            email="paymentadmin@example.com",
            password="AdminPass123!",
            role="admin",
            is_staff=True,
        )
        self.organizer = User.objects.create_user(
            username="paymentorganizer",
            email="paymentorganizer@example.com",
            password="OrganizerPass123!",
            role="organizer",
        )
        self.regular_user = User.objects.create_user(
            username="paymentuser",
            email="paymentuser@example.com",
            password="UserPass123!",
            role="user",
            phone_number="08123456789",
        )
        self.event = Event.objects.create(
            title="Payment Event",
            description="Event for payment tests",
            organizer=self.organizer,
            venue="Hall A",
            address="Jl. Payment No. 1",
            city="Surabaya",
            country="Indonesia",
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10, hours=3),
            capacity=120,
            price="125000.00",
            status="scheduled",
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="Premium",
            description="Premium access",
            price="125000.00",
            quantity=80,
        )
        self.registration = Registration.objects.create(
            user=self.regular_user,
            event=self.event,
            ticket_type=self.ticket_type,
            quantity=1,
            total_amount="125000.00",
            attendee_name="Payment User",
            attendee_email="paymentuser@example.com",
            attendee_phone="08123456789",
        )
        self.payment = Payment.objects.create(
            registration=self.registration,
            user=self.regular_user,
            amount="125000.00",
            currency="USD",
            payment_method="qris",
            status="pending",
        )

    def response_data(self, response: object) -> Any:
        return cast(Response, response).data

    def test_user_can_create_payment_from_registration_id(self):
        another_registration = Registration.objects.create(
            user=self.regular_user,
            event=Event.objects.create(
                title="Second Payment Event",
                description="Another event",
                organizer=self.organizer,
                venue="Hall B",
                address="Jl. Payment No. 2",
                city="Surabaya",
                country="Indonesia",
                start_date=timezone.now() + timedelta(days=12),
                end_date=timezone.now() + timedelta(days=12, hours=2),
                capacity=90,
                price="90000.00",
                status="scheduled",
            ),
            ticket_type=TicketType.objects.create(
                event=Event.objects.get(title="Second Payment Event"),
                name="General",
                description="General access",
                price="90000.00",
                quantity=70,
            ),
            quantity=1,
            total_amount="90000.00",
            attendee_name="Payment User",
            attendee_email="paymentuser@example.com",
            attendee_phone="08123456789",
        )
        self.api_client.force_authenticate(user=self.regular_user)

        response = cast(
            Response,
            self.api_client.post(
                reverse("payment-list-create"),
                {
                    "registration_id": str(another_registration.id),
                    "payment_method": "QRIS",
                },
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self.response_data(response)
        self.assertEqual(response_data["registration"], str(another_registration.id))
        self.assertEqual(response_data["payment_method"], "qris")
        self.assertEqual(response_data["payment_status"], "pending")

    def test_public_can_view_payment_detail(self):
        response = cast(
            Response,
            self.api_client.get(
                reverse("payment-detail", kwargs={"pk": self.payment.pk})
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertEqual(response_data["registration"], str(self.registration.id))
        self.assertEqual(response_data["payment_status"], "Pending")

    def test_admin_can_complete_payment_status(self):
        self.api_client.force_authenticate(user=self.admin_user)

        response = cast(
            Response,
            self.api_client.patch(
                reverse("update-payment-status", kwargs={"pk": self.payment.pk}),
                {
                    "status": "completed",
                    "transaction_id": "TXN-12345",
                },
                format="json",
            ),
        )

        self.payment.refresh_from_db()
        self.registration.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, "completed")
        self.assertEqual(self.payment.transaction_id, "TXN-12345")
        self.assertEqual(self.registration.payment_status, "paid")
        self.assertEqual(self.registration.status, "confirmed")

    def test_regular_user_cannot_update_payment_detail(self):
        self.api_client.force_authenticate(user=self.regular_user)

        response = cast(
            Response,
            self.api_client.put(
                reverse("payment-detail", kwargs={"pk": self.payment.pk}),
                {"payment_status": "Completed"},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
