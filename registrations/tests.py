"""Integration tests for registration API flows and permissions."""

from datetime import timedelta
from typing import Any, cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from events.models import Event
from registrations.models import Registration
from tickets.models import TicketType
from users.models import User


class RegistrationApiTests(TestCase):
    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()
        self.admin_user = User.objects.create_user(
            username="registrationadmin",
            email="registrationadmin@example.com",
            password="AdminPass123!",
            role="admin",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="registrationuser",
            email="registrationuser@example.com",
            password="UserPass123!",
            role="user",
            phone_number="08123456789",
        )
        self.organizer = User.objects.create_user(
            username="registrationorganizer",
            email="registrationorganizer@example.com",
            password="OrganizerPass123!",
            role="organizer",
        )
        self.event = Event.objects.create(
            title="Registration Event",
            description="Event for registration tests",
            organizer=self.organizer,
            venue="Conference Room",
            address="Jl. Registrasi No. 1",
            city="Jakarta",
            country="Indonesia",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5, hours=2),
            capacity=150,
            price="100000.00",
            status="scheduled",
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="General Admission",
            description="Standard ticket",
            price="75000.00",
            quantity=100,
        )
        self.registration = Registration.objects.create(
            user=self.regular_user,
            event=self.event,
            ticket_type=self.ticket_type,
            quantity=1,
            total_amount="75000.00",
            attendee_name="Registration User",
            attendee_email="registrationuser@example.com",
            attendee_phone="08123456789",
        )

    def response_data(self, response: object) -> Any:
        return cast(Response, response).data

    def test_user_can_create_registration_from_ticket_id(self):
        new_user = User.objects.create_user(
            username="newregistrationuser",
            email="newregistrationuser@example.com",
            password="UserPass456!",
            role="user",
        )
        self.api_client.force_authenticate(user=new_user)

        response = cast(
            Response,
            self.api_client.post(
                reverse("registration-list-create"),
                {
                    "ticket_id": str(self.ticket_type.id),
                    "quantity": 1,
                },
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self.response_data(response)
        self.assertEqual(response_data["ticket"], str(self.ticket_type.id))
        self.assertEqual(response_data["user"], str(new_user.id))

    def test_public_can_view_registration_detail(self):
        response = cast(
            Response,
            self.api_client.get(
                reverse("registration-detail", kwargs={"pk": self.registration.pk})
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertEqual(response_data["ticket"], str(self.ticket_type.id))
        self.assertEqual(response_data["user"], str(self.regular_user.id))

    def test_regular_user_only_sees_own_registrations(self):
        other_user = User.objects.create_user(
            username="otherregistrationuser",
            email="otherregistrationuser@example.com",
            password="UserPass789!",
            role="user",
        )
        Registration.objects.create(
            user=other_user,
            event=self.event,
            ticket_type=self.ticket_type,
            quantity=1,
            total_amount="75000.00",
            attendee_name="Other User",
            attendee_email="otherregistrationuser@example.com",
            attendee_phone="08111111111",
        )
        self.api_client.force_authenticate(user=self.regular_user)

        response = cast(
            Response, self.api_client.get(reverse("registration-list-create"))
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertEqual(len(response_data["registrations"]), 1)
        self.assertEqual(
            str(response_data["registrations"][0]["user"]), str(self.regular_user.id)
        )

    def test_owner_can_cancel_registration_via_cancel_endpoint(self):
        self.registration.status = "confirmed"
        self.registration.save(update_fields=["status"])
        self.api_client.force_authenticate(user=self.regular_user)

        response = cast(
            Response,
            self.api_client.post(
                reverse("cancel-registration", kwargs={"pk": self.registration.pk}),
                format="json",
            ),
        )

        self.registration.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.registration.status, "cancelled")
