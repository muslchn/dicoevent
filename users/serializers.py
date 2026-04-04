from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                attrs["user"] = user
                return attrs
            else:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "role", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (used by PUT/PATCH).

    We allow changing the username, email and password so that clients
    can update their profile. Passwords are handled specially (hashed)
    while other fields are applied from request payload.
    """

    password = serializers.CharField(write_only=True, required=False, min_length=8)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
        ]

    def update(self, instance, validated_data):
        # Pop out password so we can call set_password.
        password = validated_data.pop("password", None)

        username = validated_data.pop("username", None)
        if username is not None:
            instance.username = username

        email = validated_data.pop("email", None)
        if email is not None:
            instance.email = email

        # Ordinary fields.
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user roles (admin/superuser only)"""

    class Meta:
        model = User
        fields = ["role"]
