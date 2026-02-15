from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Group(models.Model):
    """Group/Organization model for managing event organizers"""
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'groups'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Custom User model with roles for DicoEvent"""
    
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('organizer', 'Event Organizer'),
        ('admin', 'Administrator'),
        ('superuser', 'Super User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_organizer(self):
        return self.role == 'organizer'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_superuser_role(self):
        return self.role == 'superuser'
    
    def has_permission_to_manage_events(self):
        return self.role in ['admin', 'superuser']
    
    def has_permission_to_manage_tickets(self):
        return self.role in ['admin', 'superuser', 'organizer']
    
    def has_permission_to_manage_registrations(self):
        return self.role in ['admin', 'superuser']
    
    def has_permission_to_manage_payments(self):
        return self.role in ['admin', 'superuser']
    
    class Meta:
        db_table = 'users'
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]