"""Integration tests for event API flows and permissions."""

from datetime import timedelta
from typing import Any, cast

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

from events.models import Event
from users.models import User


class EventApiTests(TestCase):
    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="OrganizerPass123!",
            role="organizer",
        )
        self.other_organizer = User.objects.create_user(
            username="otherorganizer",
            email="otherorganizer@example.com",
            password="OrganizerPass456!",
            role="organizer",
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
            role="admin",
            is_staff=True,
        )
        self.event = Event.objects.create(
            title="Existing Event",
            description="Existing event description",
            organizer=self.organizer,
            venue="Main Hall",
            address="Jl. Event No. 1",
            city="Bandung",
            country="Indonesia",
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=7, hours=2),
            capacity=100,
            price="50000.00",
            status="draft",
        )

    def response_data(self, response: object) -> Any:
        return cast(Response, response).data

    def test_authenticated_user_can_create_event_with_postman_field_mapping(self):
        self.api_client.force_authenticate(user=self.organizer)

        response = cast(
            Response,
            self.api_client.post(
                reverse("event-list-create"),
                {
                    "name": "Mapped Event",
                    "description": "Created through compatibility layer",
                    "location": "Auditorium",
                    "start_time": "2030-05-10 09:00",
                    "end_time": "2030-05-10 17:00",
                    "quota": 250,
                    "price": "125000.00",
                    "status": "scheduled",
                    "category": "Technology",
                },
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_event = Event.objects.get(title="Mapped Event")
        self.assertEqual(created_event.organizer, self.organizer)
        self.assertEqual(created_event.venue, "Auditorium")
        self.assertEqual(created_event.capacity, 250)
        response_data = self.response_data(response)
        self.assertEqual(response_data["name"], "Mapped Event")
        self.assertEqual(response_data["location"], "Auditorium")
        self.assertEqual(response_data["quota"], 250)

    def test_public_can_view_event_detail(self):
        response = cast(
            Response,
            self.api_client.get(reverse("event-detail", kwargs={"pk": self.event.pk})),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertEqual(response_data["name"], self.event.title)
        self.assertEqual(response_data["location"], self.event.venue)

    def test_organizer_cannot_update_someone_elses_event(self):
        self.api_client.force_authenticate(user=self.other_organizer)

        response = cast(
            Response,
            self.api_client.put(
                reverse("event-detail", kwargs={"pk": self.event.pk}),
                {"name": "Hijacked Event"},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_event(self):
        self.api_client.force_authenticate(user=self.admin_user)

        response = cast(
            Response,
            self.api_client.put(
                reverse("event-detail", kwargs={"pk": self.event.pk}),
                {
                    "name": "Admin Updated Event",
                    "location": "Updated Venue",
                    "quota": 150,
                },
                format="json",
            ),
        )

        self.event.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.event.title, "Admin Updated Event")
        self.assertEqual(self.event.venue, "Updated Venue")
        self.assertEqual(self.event.capacity, 150)

    def _build_image_upload(
        self, filename: str, size: tuple[int, int]
    ) -> SimpleUploadedFile:
        image_io = BytesIO()
        image = Image.new("RGB", size, color="white")
        image.save(image_io, format="JPEG", quality=95)
        image_io.seek(0)
        return SimpleUploadedFile(filename, image_io.read(), content_type="image/jpeg")

    def test_superuser_can_upload_event_poster(self):
        superuser = User.objects.create_user(
            username="superuser",
            email="superuser@example.com",
            password="SuperUserPass123!",
            role="superuser",
            is_superuser=True,
            is_staff=True,
        )
        self.api_client.force_authenticate(user=superuser)

        image_file = self._build_image_upload("poster-small.jpg", (100, 100))
        response = cast(
            Response,
            self.api_client.post(
                reverse("event-poster-upload"),
                {"event": str(self.event.id), "image": image_file},
                format="multipart",
            ),
        )

        self.event.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = self.response_data(response)
        self.assertIn("id", response_data)
        self.assertIn("image", response_data)
        self.assertTrue(response_data["image"])
        self.assertTrue(bool(self.event.image))

    def test_upload_event_poster_rejects_non_image(self):
        self.api_client.force_authenticate(user=self.admin_user)

        non_image_file = SimpleUploadedFile(
            "not-image.txt", b"this-is-not-an-image", content_type="text/plain"
        )
        response = cast(
            Response,
            self.api_client.post(
                reverse("event-poster-upload"),
                {"event": str(self.event.id), "image": non_image_file},
                format="multipart",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_event_poster_rejects_large_image(self):
        self.api_client.force_authenticate(user=self.admin_user)

        large_image = SimpleUploadedFile(
            "poster-large.jpg",
            b"0" * (600 * 1024),
            content_type="image/jpeg",
        )
        response = cast(
            Response,
            self.api_client.post(
                reverse("event-poster-upload"),
                {"event": str(self.event.id), "image": large_image},
                format="multipart",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_get_event_poster(self):
        self.api_client.force_authenticate(user=self.organizer)

        existing_poster = self._build_image_upload("existing-poster.jpg", (128, 128))
        self.event.image.save(existing_poster.name, existing_poster, save=False)
        self.event.save(update_fields=["image", "updated_at"])

        response = cast(
            Response,
            self.api_client.get(
                reverse("event-poster-detail", kwargs={"pk": self.event.pk})
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertIsInstance(response_data, list)
        self.assertGreaterEqual(len(response_data), 1)

    def test_events_list_out_of_range_page_returns_valid_page_payload(self):
        self.api_client.force_authenticate(user=self.organizer)

        response = cast(
            Response,
            self.api_client.get(f"{reverse('event-list-create')}?page=100"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertIn("events", response_data)
        self.assertIsInstance(response_data["events"], list)
        self.assertGreaterEqual(len(response_data["events"]), 1)
