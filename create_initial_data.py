import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dicoevent_project.settings')
django.setup()

from users.models import User
from django.contrib.auth.hashers import make_password

def create_initial_users():
    """Create initial users for testing"""
    
    # Create superuser
    if not User.objects.filter(username='Aras').exists():
        superuser = User.objects.create_user(
            username='Aras',
            email='aras@dicoevent.com',
            password='1234qwer!@#$',
            role='superuser',
            first_name='Aras',
            last_name='Admin'
        )
        # Make this user a Django superuser
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()
        print(f"Created superuser: {superuser.username}")
    
    # Create regular user
    if not User.objects.filter(username='dicoding').exists():
        user = User.objects.create_user(
            username='dicoding',
            email='user@dicoevent.com',
            password='1234qwer!@#$',
            role='user',
            first_name='Dicoding',
            last_name='User'
        )
        print(f"Created user: {user.username}")
    
    # Create admin user
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_user(
            username='admin',
            email='admin@dicoevent.com',
            password='1234qwer!@#$',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        print(f"Created admin: {admin.username}")
    
    # Create organizer user
    if not User.objects.filter(username='organizer').exists():
        organizer = User.objects.create_user(
            username='organizer',
            email='organizer@dicoevent.com',
            password='1234qwer!@#$',
            role='organizer',
            first_name='Event',
            last_name='Organizer'
        )
        print(f"Created organizer: {organizer.username}")

if __name__ == '__main__':
    create_initial_users()
    print("Initial data creation completed!")