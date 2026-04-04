"""Integration tests for ticket API flows and permissions."""

from datetime import timedelta
from typing import Any, cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from events.models import Event
from tickets.models import TicketType
from users.models import User


class TicketApiTests(TestCase):
    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()
        self.organizer = User.objects.create_user(
            username="ticketorganizer",
            email="ticketorganizer@example.com",
            password="OrganizerPass123!",
            role="organizer",
        )
        self.other_user = User.objects.create_user(
            username="ticketuser",
            email="ticketuser@example.com",
            password="UserPass123!",
            role="user",
        )
        self.event = Event.objects.create(
            title="Ticketed Event",
            description="Event for ticket tests",
            organizer=self.organizer,
            venue="Main Auditorium",
            address="Jl. Tiket No. 1",
            city="Bandung",
            country="Indonesia",
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=7, hours=3),
            capacity=200,
            price="150000.00",
            status="scheduled",
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="VIP",
            description="VIP seating",
            price="250000.00",
            quantity=50,
        )

    def response_data(self, response: object) -> Any:
        return cast(Response, response).data

    def test_organizer_can_create_ticket_type_with_legacy_field_mapping(self):
        self.api_client.force_authenticate(user=self.organizer)

        response = cast(
            Response,
            self.api_client.post(
                reverse("ticket-list"),
                {
                    "event_id": str(self.event.id),
                    "name": "Regular",
                    "description": "General admission",
                    "price": "100000.00",
                    "quota": 120,
                    "sales_start": "2026-04-01 10:00",
                    "sales_end": "2026-04-07 10:00",
                },
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_ticket_type = TicketType.objects.get(name="Regular")
        self.assertEqual(created_ticket_type.event, self.event)
        self.assertEqual(created_ticket_type.quantity, 120)
        response_data = self.response_data(response)
        self.assertEqual(response_data["event_id"], str(self.event.id))
        self.assertEqual(response_data["quota"], 120)

    def test_public_can_view_ticket_detail(self):
        response = cast(
            Response,
            self.api_client.get(
                reverse("ticket-detail", kwargs={"pk": self.ticket_type.pk})
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertEqual(response_data["name"], "VIP")
        self.assertEqual(response_data["quota"], 50)

    def test_organizer_can_generate_individual_tickets(self):
        self.api_client.force_authenticate(user=self.organizer)

        response = cast(
            Response,
            self.api_client.post(
                reverse(
                    "generate-tickets", kwargs={"ticket_type_pk": self.ticket_type.pk}
                ),
                {"count": 2},
                format="json",
            ),
        )

        self.ticket_type.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.ticket_type.sold, 2)
        response_data = self.response_data(response)
        self.assertEqual(len(response_data["tickets"]), 2)

    def test_regular_user_cannot_generate_tickets(self):
        self.api_client.force_authenticate(user=self.other_user)

        response = cast(
            Response,
            self.api_client.post(
                reverse(
                    "generate-tickets", kwargs={"ticket_type_pk": self.ticket_type.pk}
                ),
                {"count": 1},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
