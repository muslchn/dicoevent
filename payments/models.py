from django.db import models
from users.models import User
from registrations.models import Registration
import uuid


class Payment(models.Model):
    """Payment model for handling registration payments"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('e_wallet', 'E-Wallet'),
        ('cash', 'Cash'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    # Payment gateway information
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Refund information
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id or self.id} - {self.amount} {self.currency}"
    
    def process_payment(self):
        """Process the payment"""
        from django.utils import timezone
        self.status = 'processing'
        self.processed_at = timezone.now()
        self.save()
    
    def complete_payment(self, transaction_id=None, gateway_response=None):
        """Complete the payment successfully"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
        
        # Update registration payment status
        self.registration.payment_status = 'paid'
        self.registration.confirm_registration()
        self.registration.save()
    
    def fail_payment(self, reason=None, gateway_response=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            self.gateway_response = {'error': reason}
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
        
        # Update registration payment status
        self.registration.payment_status = 'unpaid'
        self.registration.save()
    
    def refund_payment(self, amount=None, reason=None):
        """Refund the payment"""
        from django.utils import timezone
        if amount is None:
            amount = self.amount
            
        self.status = 'refunded'
        self.refunded_amount = amount
        self.refund_reason = reason or ''
        self.refunded_at = timezone.now()
        self.save()
        
        # Update registration payment status
        self.registration.payment_status = 'refunded'
        self.registration.save()
    
    def cancel_payment(self):
        """Cancel the payment"""
        self.status = 'cancelled'
        self.save()
        
        # Update registration payment status
        self.registration.payment_status = 'unpaid'
        self.registration.save()
    
    class Meta:
        db_table = 'payments'
        ordering = ['-initiated_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='check_positive_amount'
            ),
            models.CheckConstraint(
                check=models.Q(refunded_amount__isnull=True) | models.Q(refunded_amount__gt=0),
                name='check_positive_refund_amount'
            )
        ]