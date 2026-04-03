#!/usr/bin/env python
import os
import sys
from datetime import timedelta

import django
from django.db.models import Q
from django.utils import timezone


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dicoevent_project.settings")
    django.setup()


def load_models():
    from django.contrib.auth import get_user_model
    from events.models import Event
    from payments.models import Payment
    from registrations.models import Registration
    from tickets.models import Ticket, TicketType
    from users.models import Group

    return get_user_model(), Group, Event, TicketType, Ticket, Registration, Payment


def ensure_user(User, *, username: str, email: str, password: str, **defaults):
    existing_user = User.objects.filter(Q(username=username) | Q(email=email)).first()
    created = existing_user is None

    if created:
        user = User(username=username, email=email, **defaults)
    else:
        user = existing_user
        user.username = username
        user.email = email
        for field, value in defaults.items():
            setattr(user, field, value)

    user.set_password(password)
    user.save()
    return user, created


def create_test_users():
    """Create test users with different roles"""
    print("Creating test users...")
    User, _, _, _, _, _, _ = load_models()

    # Create superuser
    superuser, created = ensure_user(
        User,
        username="superuser",
        email="superuser@dicoevent.com",
        password="superpassword123",
        first_name="Super",
        last_name="User",
        phone_number="+6281234567890",
        role="superuser",
    )
    superuser.is_superuser = True
    superuser.is_staff = True
    superuser.save(update_fields=["is_superuser", "is_staff"])
    print(f"{'Created' if created else 'Updated'} superuser: {superuser.username}")

    # Create admin user
    admin, created = ensure_user(
        User,
        username="admin",
        email="admin@dicoevent.com",
        password="adminpassword123",
        first_name="Admin",
        last_name="User",
        phone_number="+6281234567891",
        role="admin",
    )
    print(f"{'Created' if created else 'Updated'} admin: {admin.username}")

    # Create organizer user
    organizer, created = ensure_user(
        User,
        username="organizer",
        email="organizer@dicoevent.com",
        password="organizerpassword123",
        first_name="Organizer",
        last_name="User",
        phone_number="+6281234567892",
        role="organizer",
    )
    print(f"{'Created' if created else 'Updated'} organizer: {organizer.username}")

    # Create regular user
    user, created = ensure_user(
        User,
        username="user",
        email="testuser@dicoevent.com",
        password="userpassword123",
        first_name="Regular",
        last_name="User",
        phone_number="+6281234567893",
        role="user",
    )
    print(f"{'Created' if created else 'Updated'} user: {user.username}")


def create_test_groups():
    """Create test groups/organizations"""
    print("Creating test groups...")
    _, Group, _, _, _, _, _ = load_models()

    group, created = Group.objects.update_or_create(
        name="Test Organization",
        defaults={"description": "A test organization for testing purposes"},
    )
    print(f"{'Created' if created else 'Updated'} group: {group.name}")


def create_test_events():
    """Create test events"""
    print("Creating test events...")
    User, Group, Event, _, _, _, _ = load_models()

    organizer = User.objects.get(username="organizer")
    Group.objects.get(name="Test Organization")

    start_date = timezone.now() + timedelta(days=10)
    end_date = start_date + timedelta(days=1)
    event, created = Event.objects.update_or_create(
        title="Test Event",
        defaults={
            "description": "A test event for API testing",
            "organizer": organizer,
            "venue": "Test Venue",
            "address": "123 Test Street",
            "city": "Test City",
            "country": "Indonesia",
            "start_date": start_date,
            "end_date": end_date,
            "capacity": 100,
            "price": 0.00,
            "status": "published",
        },
    )
    print(f"{'Created' if created else 'Updated'} event: {event.title}")
    return event


def create_test_ticket_types(event):
    """Create test ticket types"""
    print("Creating test ticket types...")
    _, _, _, TicketType, _, _, _ = load_models()

    if not event:
        return None

    ticket_type, created = TicketType.objects.update_or_create(
        event=event,
        name="Standard Ticket",
        defaults={
            "description": "Standard admission ticket",
            "price": 50.00,
            "quantity": 50,
            "sold": 0,
            "is_active": True,
        },
    )
    print(f"{'Created' if created else 'Updated'} ticket type: {ticket_type.name}")
    return ticket_type


def create_test_tickets(ticket_type):
    """Create individual tickets"""
    print("Creating test tickets...")
    _, _, _, _, Ticket, _, _ = load_models()

    if not ticket_type:
        return

    created_count = 0
    stable_prefix = ticket_type.id.hex[:8].upper()
    for index in range(1, 6):
        _, created = Ticket.objects.get_or_create(
            ticket_type=ticket_type,
            code=f"TEST-{stable_prefix}-{index:02d}",
        )
        created_count += int(created)

    if created_count:
        print(f"Created {created_count} individual tickets")
    else:
        print("Individual tickets already exist")


def create_test_registrations(event, ticket_type):
    """Create test registrations"""
    print("Creating test registrations...")
    User, _, _, _, _, Registration, _ = load_models()

    if not (event and ticket_type):
        return None

    user = User.objects.get(username="user")
    registration, created = Registration.objects.update_or_create(
        user=user,
        event=event,
        defaults={
            "ticket_type": ticket_type,
            "status": "confirmed",
            "payment_status": "paid",
            "quantity": 1,
            "total_amount": ticket_type.price,
            "attendee_name": f"{user.first_name} {user.last_name}",
            "attendee_email": user.email,
            "attendee_phone": getattr(user, "phone_number", "") or "",
        },
    )
    print(
        f"{'Created' if created else 'Updated'} registration for user: {user.username}"
    )
    return registration


def create_test_payments(registration):
    """Create test payments"""
    print("Creating test payments...")
    _, _, _, _, _, _, Payment = load_models()

    if not registration:
        return

    payment, created = Payment.objects.update_or_create(
        registration=registration,
        defaults={
            "user": registration.user,
            "amount": registration.total_amount,
            "currency": "USD",
            "payment_method": "credit_card",
            "status": "completed",
        },
    )
    print(
        f"{'Created' if created else 'Updated'} payment for registration: {payment.registration.id}"
    )


def main():
    """Main function to setup all test data"""
    setup_django()
    print("Setting up test data for Newman tests...")

    try:
        create_test_users()
        create_test_groups()
        event = create_test_events()
        ticket_type = create_test_ticket_types(event)
        create_test_tickets(ticket_type)
        registration = create_test_registrations(event, ticket_type)
        create_test_payments(registration)

        print("\n✅ Test data setup completed successfully!")
        print("\nTest credentials:")
        print("- Superuser: superuser / superpassword123")
        print("- Admin: admin / adminpassword123")
        print("- Organizer: organizer / organizerpassword123")
        print("- User: user / userpassword123")

    except Exception as e:
        print(f"\n❌ Error setting up test data: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
