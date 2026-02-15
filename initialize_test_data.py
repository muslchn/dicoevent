#!/usr/bin/env python
"""Initialize test data for Newman testing"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dicoevent_project.settings')
django.setup()

from users.models import User, Group
from events.models import Event
from tickets.models import TicketType
from registrations.models import Registration
from payments.models import Payment
import uuid
from datetime import datetime, timedelta

def create_test_users():
    """Create test users required for Newman tests"""
    print("Creating test users...")
    
    # Create superuser
    if not User.objects.filter(username='Aras').exists():
        superuser = User.objects.create_user(
            username='Aras',
            email='aras@dicoevent.com',
            password='1234qwer!@#$',
            first_name='Aras',
            last_name='Admin',
            role='superuser'
        )
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()
        print(f"✓ Created superuser: {superuser.username}")
    
    # Create regular user
    if not User.objects.filter(username='dicoding').exists():
        user = User.objects.create_user(
            username='dicoding',
            email='user@dicoevent.com',
            password='1234qwer!@#$',
            first_name='Dicoding',
            last_name='User',
            role='user'
        )
        print(f"✓ Created user: {user.username}")

def create_test_groups():
    """Create test groups/organizers"""
    print("Creating test groups...")
    
    if not Group.objects.filter(name='Dicoding Organizer').exists():
        group = Group.objects.create(
            name='Dicoding Organizer',
            description='Official Dicoding event organizer group'
        )
        print(f"✓ Created group: {group.name}")

def create_test_events():
    """Create test events"""
    print("Creating test events...")
    
    organizer = User.objects.get(username='Aras')
    
    if not Event.objects.filter(title='Dicoding Tech Conference').exists():
        event = Event.objects.create(
            title='Dicoding Tech Conference',
            description='Annual technology conference by Dicoding',
            organizer=organizer,
            venue='Jakarta Convention Center',
            address='Jl. Jenderal Gatot Subroto Kav. 21-23',
            city='Jakarta',
            country='Indonesia',
            start_date=datetime.now() + timedelta(days=30),
            end_date=datetime.now() + timedelta(days=32),
            capacity=1000,
            price=0.00,
            status='published'
        )
        print(f"✓ Created event: {event.title}")

def create_test_tickets():
    """Create test ticket types"""
    print("Creating test tickets...")
    
    event = Event.objects.get(title='Dicoding Tech Conference')
    
    if not TicketType.objects.filter(name='General Admission').exists():
        ticket = TicketType.objects.create(
            event=event,
            name='General Admission',
            description='Standard conference access',
            price=500000.00,
            quantity=500
        )
        print(f"✓ Created ticket: {ticket.name}")

def initialize_test_data():
    """Initialize all test data"""
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

if __name__ == '__main__':
    initialize_test_data()