import os

import django
from django.db.models import Q


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dicoevent_project.settings")
    django.setup()


def load_user_model():
    from users.models import User

    return User


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


def create_initial_users():
    """Create initial users for testing"""
    User = load_user_model()

    # Create superuser
    superuser, created = ensure_user(
        User,
        username="Aras",
        email="aras@dicoevent.com",
        password="1234qwer!@#$",
        role="superuser",
        first_name="Aras",
        last_name="Admin",
    )
    superuser.is_superuser = True
    superuser.is_staff = True
    superuser.save(update_fields=["is_superuser", "is_staff"])
    if created:
        print(f"Created superuser: {superuser.username}")
    else:
        print(f"Updated superuser: {superuser.username}")

    # Create regular user
    user, created = ensure_user(
        User,
        username="dicoding",
        email="user@dicoevent.com",
        password="1234qwer!@#$",
        role="user",
        first_name="Dicoding",
        last_name="User",
    )
    if created:
        print(f"Created user: {user.username}")
    else:
        print(f"Updated user: {user.username}")

    # Create admin user
    admin, created = ensure_user(
        User,
        username="admin",
        email="admin@dicoevent.com",
        password="1234qwer!@#$",
        role="admin",
        first_name="Admin",
        last_name="User",
    )
    if created:
        print(f"Created admin: {admin.username}")
    else:
        print(f"Updated admin: {admin.username}")

    # Create organizer user
    organizer, created = ensure_user(
        User,
        username="organizer",
        email="organizer@dicoevent.com",
        password="1234qwer!@#$",
        role="organizer",
        first_name="Event",
        last_name="Organizer",
    )
    if created:
        print(f"Created organizer: {organizer.username}")
    else:
        print(f"Updated organizer: {organizer.username}")


if __name__ == "__main__":
    setup_django()
    create_initial_users()
    print("Initial data creation completed!")
