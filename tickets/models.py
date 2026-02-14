from django.db import models
from events.models import Event
import uuid


class TicketType(models.Model):
    """Ticket type model for different ticket categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    sold = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"
    
    def available_quantity(self):
        return max(0, self.quantity - self.sold)
    
    def is_sold_out(self):
        return self.sold >= self.quantity
    
    class Meta:
        db_table = 'ticket_types'
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='check_non_negative_price'
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='check_positive_quantity'
            ),
            models.CheckConstraint(
                check=models.Q(sold__gte=0),
                name='check_non_negative_sold'
            ),
            models.CheckConstraint(
                check=models.Q(sold__lte=models.F('quantity')),
                name='check_sold_not_exceed_quantity'
            )
        ]


class Ticket(models.Model):
    """Individual ticket instance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='tickets')
    code = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Ticket {self.code} - {self.ticket_type.name}"
    
    def mark_as_used(self):
        """Mark ticket as used"""
        from django.utils import timezone
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = 'tickets'
        ordering = ['-issued_at']