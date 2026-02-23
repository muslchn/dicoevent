from django.db import models
from users.models import User
import uuid


class Event(models.Model):
    """Event model for DicoEvent system"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),  # legacy status used in Postman tests
        ("published", "Published"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organized_events"
    )
    venue = models.CharField(max_length=300)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%Y-%m-%d')}"

    def is_full(self):
        """Check if event has reached capacity"""
        from registrations.models import Registration

        confirmed_registrations = Registration.objects.filter(
            event=self, status="confirmed"
        ).count()
        return confirmed_registrations >= self.capacity

    def available_spots(self):
        """Calculate available spots"""
        from registrations.models import Registration

        confirmed_registrations = Registration.objects.filter(
            event=self, status="confirmed"
        ).count()
        return max(0, self.capacity - confirmed_registrations)

    class Meta:
        db_table = "events"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F("start_date")),
                name="check_event_dates",
            ),
            models.CheckConstraint(
                check=models.Q(capacity__gt=0), name="check_positive_capacity"
            ),
        ]
