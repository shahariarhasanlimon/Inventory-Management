from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Used for viewing and updating the logged-in user's own profile.
    Username/email are read-only here on purpose -- changing your login
    identity isn't part of "profile management" for this assignment.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "date_of_birth",
        ]
        read_only_fields = ["id", "username", "email"]

    def validate_phone_number(self, value):
        if value and not value.replace("+", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(
                "Phone number may only contain digits, spaces, and a leading +."
            )
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """
    Minimal registration serializer so the API is self-contained
    (create a user, then log in and manage the profile/inventory).
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
