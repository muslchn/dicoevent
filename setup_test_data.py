#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dicoevent_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Group
from events.models import Event
from tickets.models import TicketType, Ticket
from registrations.models import Registration
from payments.models import Payment
import uuid
from datetime import datetime, timedelta

User = get_user_model()

def create_test_users():
    """Create test users with different roles"""
    print("Creating test users...")
    
    # Create superuser
    try:
        if not User.objects.filter(username='superuser').exists():
            superuser = User.objects.create_user(
                username='superuser',
                email='superuser@dicoevent.com',
                password='superpassword123',
                first_name='Super',
                last_name='User',
                phone_number='+6281234567890',
                role='superuser'
            )
            superuser.is_superuser = True
            superuser.is_staff = True
            superuser.save()
            print(f"Created superuser: {superuser.username}")
        else:
            print("Superuser already exists")
    except Exception as e:
        print(f"Error creating superuser: {e}")
    
    # Create admin user
    try:
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@dicoevent.com',
                password='adminpassword123',
                first_name='Admin',
                last_name='User',
                phone_number='+6281234567891',
                role='admin'
            )
            print(f"Created admin: {admin.username}")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin: {e}")
    
    # Create organizer user
    try:
        if not User.objects.filter(username='organizer').exists():
            organizer = User.objects.create_user(
                username='organizer',
                email='organizer@dicoevent.com',
                password='organizerpassword123',
                first_name='Organizer',
                last_name='User',
                phone_number='+6281234567892',
                role='organizer'
            )
            print(f"Created organizer: {organizer.username}")
        else:
            print("Organizer user already exists")
    except Exception as e:
        print(f"Error creating organizer: {e}")
    
    # Create regular user
    try:
        if not User.objects.filter(username='user').exists():
            user = User.objects.create_user(
                username='user',
                email='user@dicoevent.com',
                password='userpassword123',
                first_name='Regular',
                last_name='User',
                phone_number='+6281234567893',
                role='user'
            )
            print(f"Created user: {user.username}")
        else:
            print("Regular user already exists")
    except Exception as e:
        print(f"Error creating user: {e}")

def create_test_groups():
    """Create test groups/organizations"""
    print("Creating test groups...")
    
    try:
        if not Group.objects.filter(name='Test Organization').exists():
            group = Group.objects.create(
                name='Test Organization',
                description='A test organization for testing purposes'
            )
            print(f"Created group: {group.name}")
        else:
            print("Test group already exists")
    except Exception as e:
        print(f"Error creating group: {e}")

def create_test_events():
    """Create test events"""
    print("Creating test events...")
    
    try:
        organizer = User.objects.get(username='organizer')
        group = Group.objects.get(name='Test Organization')
        
        # Create event organized by the test organizer
        if not Event.objects.filter(title='Test Event').exists():
            event = Event.objects.create(
                title='Test Event',
                description='A test event for API testing',
                organizer=organizer,
                venue='Test Venue',
                address='123 Test Street',
                city='Test City',
                country='Indonesia',
                start_date=datetime.now() + timedelta(days=10),
                end_date=datetime.now() + timedelta(days=11),
                capacity=100,
                price=0.00,
                status='published'
            )
            print(f"Created event: {event.title}")
        else:
            print("Test event already exists")
    except Exception as e:
        print(f"Error creating event: {e}")

def create_test_ticket_types(event):
    """Create test ticket types"""
    print("Creating test ticket types...")
    
    try:
        if event and not TicketType.objects.filter(event=event, name='Standard Ticket').exists():
            ticket_type = TicketType.objects.create(
                event=event,
                name='Standard Ticket',
                description='Standard admission ticket',
                price=50.00,
                quantity=50
            )
            print(f"Created ticket type: {ticket_type.name}")
            return ticket_type
        elif event:
            print("Test ticket type already exists")
            return TicketType.objects.get(event=event, name='Standard Ticket')
    except Exception as e:
        print(f"Error creating ticket type: {e}")
    return None

def create_test_tickets(ticket_type):
    """Create individual tickets"""
    print("Creating test tickets...")
    
    try:
        if ticket_type:
            # Create a few individual tickets
            for i in range(5):
                ticket = Ticket.objects.create(
                    ticket_type=ticket_type,
                    code=f'TEST-{uuid.uuid4().hex[:8].upper()}'
                )
            print(f"Created {min(5, ticket_type.quantity - ticket_type.sold)} individual tickets")
    except Exception as e:
        print(f"Error creating tickets: {e}")

def create_test_registrations(event, ticket_type):
    """Create test registrations"""
    print("Creating test registrations...")
    
    try:
        if event and ticket_type:
            user = User.objects.get(username='user')
            
            # Check if registration already exists
            existing_reg = Registration.objects.filter(user=user, event=event).first()
            if not existing_reg:
                registration = Registration.objects.create(
                    user=user,
                    event=event,
                    ticket_type=ticket_type,
                    status='confirmed',
                    payment_status='paid',
                    quantity=1,
                    total_amount=ticket_type.price,
                    attendee_name=f"{user.first_name} {user.last_name}",
                    attendee_email=user.email,
                    attendee_phone=user.phone_number
                )
                print(f"Created registration for user: {user.username}")
                return registration
            else:
                print("Test registration already exists")
                return existing_reg
    except Exception as e:
        print(f"Error creating registration: {e}")
    return None

def create_test_payments(registration):
    """Create test payments"""
    print("Creating test payments...")
    
    try:
        if registration and not Payment.objects.filter(registration=registration).exists():
            payment = Payment.objects.create(
                registration=registration,
                amount=registration.total_amount,
                payment_method='credit_card',
                status='completed'
            )
            print(f"Created payment for registration: {registration.id}")
    except Exception as e:
        print(f"Error creating payment: {e}")

def main():
    """Main function to setup all test data"""
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

if __name__ == '__main__':
    main()