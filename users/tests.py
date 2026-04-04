"""Integration tests for user-facing API flows."""

from typing import Any, cast

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from users.models import User


class UserApiTests(TestCase):
    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="AdminPass123!",
            role="admin",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="RegularPass123!",
            role="user",
        )

    def response_data(self, response: object) -> Any:
        return cast(Response, response).data

    def test_public_user_registration_creates_user(self):
        response = cast(
            Response,
            self.api_client.post(
                reverse("user-list-create"),
                {
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "User",
                    "phone_number": "08123456789",
                },
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        created_user = User.objects.get(username="newuser")
        self.assertTrue(created_user.check_password("StrongPass123!"))
        self.assertEqual(self.response_data(response)["email"], "newuser@example.com")

    def test_login_returns_jwt_tokens_for_valid_credentials(self):
        response = cast(
            Response,
            self.api_client.post(
                reverse("user-login"),
                {"username": "regularuser", "password": "RegularPass123!"},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertIn("refresh", response_data)
        self.assertIn("access", response_data)

    def test_regular_user_cannot_list_all_users(self):
        self.api_client.force_authenticate(user=self.regular_user)

        response = cast(Response, self.api_client.get(reverse("user-list-create")))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_all_users(self):
        self.api_client.force_authenticate(user=self.admin_user)

        response = cast(Response, self.api_client.get(reverse("user-list-create")))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = self.response_data(response)
        self.assertIn("users", response_data)
        self.assertGreaterEqual(len(response_data["users"]), 2)

    def test_user_update_uses_request_username(self):
        self.api_client.force_authenticate(user=self.regular_user)
        user_detail_url = reverse("user-detail", kwargs={"pk": self.regular_user.pk})
        response = cast(
            Response,
            self.api_client.put(
                user_detail_url,
                {
                    "username": "updatedusername",
                    "email": "updated@example.com",
                    "first_name": "Updated",
                },
                format="json",
            ),
        )

        self.regular_user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.regular_user.username, "updatedusername")
        self.assertEqual(self.regular_user.email, "updated@example.com")
