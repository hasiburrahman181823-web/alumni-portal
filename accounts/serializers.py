from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "department", "graduation_year", "job_title", "company", "location", "phone", "linkedin_url")
        read_only_fields = ("avatar",)  # upload through /api/me/avatar/


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "profile")
        read_only_fields = ("id", "username", "role")  # a user can never change their own role

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password")

    def validate_password(self, value):
        validate_password(value)  # runs the AUTH_PASSWORD_VALIDATORS
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  # hashes the password, role = USER


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("avatar",)


class AlumniSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Profile
        fields = ("username", "full_name", "avatar", "bio", "department", "graduation_year", "job_title", "company", "location")
