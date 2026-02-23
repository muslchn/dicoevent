from rest_framework import serializers  # type: ignore[import]
from .models import Registration
from users.serializers import UserSerializer
from events.serializers import EventSerializer
from tickets.serializers import TicketTypeSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Registration model"""

    user_detail = UserSerializer(source="user", read_only=True)
    event_detail = EventSerializer(source="event", read_only=True)
    ticket_type_detail = TicketTypeSerializer(source="ticket_type", read_only=True)

    # contact info may be omitted; defaults are filled in create()
    attendee_name = serializers.CharField(required=False)
    attendee_email = serializers.EmailField(required=False)
    attendee_phone = serializers.CharField(required=False)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "user_detail",
            "event",
            "event_detail",
            "ticket_type",
            "ticket_type_detail",
            "status",
            "payment_status",
            "quantity",
            "total_amount",
            "attendee_name",
            "attendee_email",
            "attendee_phone",
            "special_requirements",
            "registered_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_detail",
            "event_detail",
            "ticket_type_detail",
            "total_amount",
            "registered_at",
            "updated_at",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        event = attrs.get("event")
        ticket_type = attrs.get("ticket_type")
        quantity = attrs.get("quantity", 1)

        # Check if user is trying to register for their own event
        # Superusers and admins should be able to register regardless of organizer
        if event and event.organizer == user:
            # allow bypass for elevated roles
            if not (user.is_superuser_role() or user.is_admin()):
                raise serializers.ValidationError(
                    "You cannot register for your own event"
                )

        # Check if event has available capacity
        if event and event.is_full():
            raise serializers.ValidationError("Event has reached maximum capacity")

        # Check if ticket type belongs to the event
        if ticket_type and event and ticket_type.event != event:
            raise serializers.ValidationError(
                "Ticket type does not belong to this event"
            )

        # Check ticket availability
        if ticket_type and quantity > ticket_type.available_quantity():
            raise serializers.ValidationError(
                f"Not enough tickets available. Only {ticket_type.available_quantity()} remaining."
            )

        # Check if registration already exists
        if self.instance is None:  # Creating new registration
            existing_registration = Registration.objects.filter(
                user=user, event=event
            ).exclude(status="cancelled")

            if existing_registration.exists():
                raise serializers.ValidationError(
                    "You are already registered for this event"
                )

        return attrs

    def create(self, validated_data):
        # Calculate total amount
        ticket_type = validated_data["ticket_type"]
        quantity = validated_data.get("quantity", 1)
        validated_data["total_amount"] = ticket_type.price * quantity

        # Set or default attendee info from user
        user = self.context["request"].user
        if not validated_data.get("attendee_name"):
            validated_data["attendee_name"] = (
                f"{user.first_name} {user.last_name}".strip() or user.username
            )
        if not validated_data.get("attendee_email"):
            validated_data["attendee_email"] = user.email
        # phone number may be blank; ensure we never insert None
        if not validated_data.get("attendee_phone"):
            validated_data["attendee_phone"] = getattr(user, "phone_number", "") or ""

        return super().create(validated_data)


class RegistrationCreateSerializer(RegistrationSerializer):
    """Serializer for creating registrations"""

    class Meta(RegistrationSerializer.Meta):
        read_only_fields = [
            "id",
            "user",
            "user_detail",
            "event_detail",
            "ticket_type_detail",
            "status",
            "payment_status",
            "total_amount",
            "registered_at",
            "updated_at",
        ]


class RegistrationUpdateSerializer(RegistrationSerializer):
    """Serializer for updating registrations"""

    class Meta(RegistrationSerializer.Meta):
        read_only_fields = [
            "id",
            "user",
            "user_detail",
            "event",
            "event_detail",
            "ticket_type",
            "ticket_type_detail",
            "total_amount",
            "registered_at",
            "updated_at",
            "attendee_name",
            "attendee_email",
            "attendee_phone",
        ]


class RegistrationStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating registration status"""

    class Meta:
        model = Registration
        fields = ["status"]
