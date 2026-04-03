#!/usr/bin/env python
"""Initialize test data for Newman testing"""

import os
import sys
from datetime import timedelta

import django
from django.utils import timezone


def setup_django() -> None:
    """Configure Django before importing ORM models."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dicoevent_project.settings")
    django.setup()


def load_models():
    """Import and return the ORM models needed by the seed script."""
    from events.models import Event
    from tickets.models import TicketType
    from users.models import Group, User

    return User, Group, Event, TicketType


def create_test_users():
    """Create test users required for Newman tests"""
    print("Creating test users...")
    User, _, _, _ = load_models()

    # Create superuser
    if not User.objects.filter(username="Aras").exists():
        superuser = User.objects.create_user(
            username="Aras",
            email="aras@dicoevent.com",
            password="1234qwer!@#$",
            first_name="Aras",
            last_name="Admin",
            role="superuser",
        )
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()
        print(f"✓ Created superuser: {superuser.username}")

    # Create regular user
    if not User.objects.filter(username="dicoding").exists():
        user = User.objects.create_user(
            username="dicoding",
            email="user@dicoevent.com",
            password="1234qwer!@#$",
            first_name="Dicoding",
            last_name="User",
            role="user",
        )
        print(f"✓ Created user: {user.username}")


def create_test_groups():
    """Create test groups/organizers"""
    print("Creating test groups...")
    _, Group, _, _ = load_models()

    if not Group.objects.filter(name="Dicoding Organizer").exists():
        group = Group.objects.create(
            name="Dicoding Organizer",
            description="Official Dicoding event organizer group",
        )
        print(f"✓ Created group: {group.name}")


def create_test_events():
    """Create test events"""
    print("Creating test events...")
    User, _, Event, _ = load_models()

    organizer = User.objects.get(username="Aras")

    if not Event.objects.filter(title="Dicoding Tech Conference").exists():
        start_date = timezone.now() + timedelta(days=30)
        end_date = start_date + timedelta(days=2)
        event = Event.objects.create(
            title="Dicoding Tech Conference",
            description="Annual technology conference by Dicoding",
            organizer=organizer,
            venue="Jakarta Convention Center",
            address="Jl. Jenderal Gatot Subroto Kav. 21-23",
            city="Jakarta",
            country="Indonesia",
            start_date=start_date,
            end_date=end_date,
            capacity=1000,
            price=0.00,
            status="published",
        )
        print(f"✓ Created event: {event.title}")


def create_test_tickets():
    """Create test ticket types"""
    print("Creating test tickets...")
    _, _, Event, TicketType = load_models()

    event = Event.objects.get(title="Dicoding Tech Conference")

    if not TicketType.objects.filter(name="General Admission").exists():
        ticket = TicketType.objects.create(
            event=event,
            name="General Admission",
            description="Standard conference access",
            price=500000.00,
            quantity=500,
        )
        print(f"✓ Created ticket: {ticket.name}")


def initialize_test_data():
    """Initialize all test data"""
    setup_django()
    print("Initializing test data for Newman tests...")
    print("=" * 50)

    try:
        create_test_users()
        create_test_groups()
        create_test_events()
        create_test_tickets()

        print("=" * 50)
        print("✓ Test data initialization completed successfully!")
        print("\nReady for Newman testing.")

    except Exception as e:
        print(f"❌ Error initializing test data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    initialize_test_data()
