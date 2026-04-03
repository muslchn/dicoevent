from rest_framework import serializers
from .models import Payment
from users.serializers import UserSerializer
from registrations.serializers import RegistrationSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""

    user_detail = UserSerializer(source="user", read_only=True)
    registration_detail = RegistrationSerializer(source="registration", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "registration",
            "registration_detail",
            "user",
            "user_detail",
            "amount",
            "currency",
            "status",
            "payment_method",
            "transaction_id",
            "gateway_response",
            "initiated_at",
            "processed_at",
            "completed_at",
            "refunded_amount",
            "refund_reason",
            "refunded_at",
        ]
        read_only_fields = [
            "id",
            "user_detail",
            "registration_detail",
            "amount",
            "currency",
            "initiated_at",
            "processed_at",
            "completed_at",
            "refunded_at",
        ]

    def validate(self, attrs):
        registration = attrs.get("registration")

        if registration:
            # Check if registration already has a payment
            if hasattr(registration, "payment"):
                raise serializers.ValidationError(
                    "Payment already exists for this registration"
                )

            # Check if registration is eligible for payment
            if registration.status == "cancelled":
                raise serializers.ValidationError(
                    "Cannot create payment for cancelled registration"
                )

            # Set amount from registration
            attrs["amount"] = registration.total_amount
            attrs["user"] = registration.user
            attrs["currency"] = "USD"  # Default currency

        return attrs


class PaymentCreateSerializer(PaymentSerializer):
    """Serializer for creating payments"""

    class Meta(PaymentSerializer.Meta):
        read_only_fields = [
            "id",
            "user",
            "user_detail",
            "registration_detail",
            "amount",
            "currency",
            "status",
            "initiated_at",
            "processed_at",
            "completed_at",
            "refunded_at",
        ]


class PaymentUpdateSerializer(PaymentSerializer):
    """Serializer for updating payments"""

    class Meta(PaymentSerializer.Meta):
        read_only_fields = [
            "id",
            "registration",
            "user",
            "user_detail",
            "registration_detail",
            "amount",
            "currency",
            "initiated_at",
            "processed_at",
            "completed_at",
            "refunded_at",
        ]


class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payment status"""

    class Meta:
        model = Payment
        fields = ["status", "transaction_id", "gateway_response"]


class RefundPaymentSerializer(serializers.Serializer):
    """Serializer for refunding payments"""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than 0")
        return value
