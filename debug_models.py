import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dicoevent_project.settings')
django.setup()

print("Django setup complete")

# Test imports
try:
    from users.models import User
    print("✓ User model imported successfully")
except Exception as e:
    print(f"✗ Error importing User model: {e}")

try:
    from events.models import Event
    print("✓ Event model imported successfully")
except Exception as e:
    print(f"✗ Error importing Event model: {e}")

try:
    from tickets.models import TicketType, Ticket
    print("✓ Ticket models imported successfully")
except Exception as e:
    print(f"✗ Error importing Ticket models: {e}")

try:
    from registrations.models import Registration
    print("✓ Registration model imported successfully")
except Exception as e:
    print(f"✗ Error importing Registration model: {e}")

try:
    from payments.models import Payment
    print("✓ Payment model imported successfully")
except Exception as e:
    print(f"✗ Error importing Payment model: {e}")