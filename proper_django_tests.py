import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from events.models import Event
from tickets.models import TicketType
from registrations.models import Registration
import uuid

User = get_user_model()

class DicoEventAPITestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.superuser = User.objects.create_user(
            username='test_super',
            email='super@test.com',
            password='testpass123',
            role='superuser'
        )
        
        self.regular_user = User.objects.create_user(
            username='test_regular',
            email='regular@test.com',
            password='testpass123',
            role='user'
        )
        
        # Create API clients
        self.client = APIClient()
        self.authenticated_client = APIClient()
        self.authenticated_client.force_authenticate(user=self.regular_user)
        
        self.super_client = APIClient()
        self.super_client.force_authenticate(user=self.superuser)
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('username', response.data)
    
    def test_user_login(self):
        """Test user login endpoint"""
        data = {
            'username': 'test_regular',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_list_users_superuser_access(self):
        """Test that superusers can list all users"""
        response = self.super_client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertIsInstance(response.data['results'], list)
        else:
            self.assertIsInstance(response.data, list)
    
    def test_list_users_regular_user_forbidden(self):
        """Test that regular users cannot list all users"""
        response = self.authenticated_client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_event(self):
        """Test event creation by superuser"""
        data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'venue': 'Test Venue',
            'address': 'Test Address',
            'city': 'Test City',
            'country': 'Test Country',
            'start_date': '2024-12-01T10:00:00Z',
            'end_date': '2024-12-01T18:00:00Z',
            'capacity': 100,
            'price': 50.00,
            'status': 'draft'
        }
        
        response = self.super_client.post('/api/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
    
    def test_list_events_authenticated(self):
        """Test that authenticated users can list events"""
        response = self.authenticated_client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_ticket_type(self):
        """Test ticket type creation"""
        # First create an event
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            organizer=self.superuser,
            venue='Test Venue',
            address='Test Address',
            city='Test City',
            country='Test Country',
            start_date='2024-12-01T10:00:00Z',
            end_date='2024-12-01T18:00:00Z',
            capacity=100,
            price=50.00,
            status='draft'
        )
        
        data = {
            'event': str(event.id),
            'name': 'General Admission',
            'description': 'General admission ticket',
            'price': 50.00,
            'quantity': 100
        }
        
        response = self.super_client.post('/api/ticket-types/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
    
    def test_create_registration(self):
        """Test registration creation"""
        # Create event and ticket type
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            organizer=self.superuser,
            venue='Test Venue',
            address='Test Address',
            city='Test City',
            country='Test Country',
            start_date='2024-12-01T10:00:00Z',
            end_date='2024-12-01T18:00:00Z',
            capacity=100,
            price=50.00,
            status='draft'
        )
        
        ticket_type = TicketType.objects.create(
            event=event,
            name='General Admission',
            description='General admission ticket',
            price=50.00,
            quantity=100
        )
        
        data = {
            'event': str(event.id),
            'ticket_type': str(ticket_type.id),
            'quantity': 1,
            'total_amount': 50.00,
            'attendee_name': 'Test Attendee',
            'attendee_email': 'attendee@test.com',
            'attendee_phone': '+1234567890'
        }
        
        response = self.authenticated_client.post('/api/registrations/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

# Integration test function for pytest
@pytest.mark.django_db
def test_api_integration():
    """Integration test to verify overall API functionality"""
    client = APIClient()
    
    # Test registration
    register_data = {
        'username': f'integration_test_{uuid.uuid4().hex[:8]}',
        'email': 'integration@test.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'Integration',
        'last_name': 'Test'
    }
    
    response = client.post('/api/register/', register_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    
    # Test login
    login_data = {
        'username': register_data['username'],
        'password': register_data['password']
    }
    
    response = client.post('/api/login/', login_data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    
    # Test authenticated access
    access_token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    response = client.get('/api/events/')
    assert response.status_code == status.HTTP_200_OK