from django.db import models
from users.models import User
from events.models import Event
from tickets.models import TicketType
import uuid


class Registration(models.Model):
    """Registration model for event attendance tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Contact information at time of registration
    attendee_name = models.CharField(max_length=200)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=20)
    
    # Special requirements
    special_requirements = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
    
    def calculate_total_amount(self):
        """Calculate total amount based on ticket type price and quantity"""
        return self.ticket_type.price * self.quantity
    
    def confirm_registration(self):
        """Confirm registration and update status"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save()
            return True
        return False
    
    def cancel_registration(self):
        """Cancel registration"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def mark_as_attended(self):
        """Mark registration as attended"""
        if self.status == 'confirmed':
            self.status = 'attended'
            self.save()
            return True
        return False
    
    class Meta:
        db_table = 'registrations'
        ordering = ['-registered_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='check_registration_positive_quantity'
            ),
            models.CheckConstraint(
                check=models.Q(total_amount__gte=0),
                name='check_non_negative_amount'
            ),
            models.UniqueConstraint(
                fields=['user', 'event'],
                name='unique_user_event_registration'
            )
        ]