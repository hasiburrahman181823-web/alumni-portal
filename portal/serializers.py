from rest_framework import serializers

from .models import Event, JobPost


class JobPostSerializer(serializers.ModelSerializer):
    posted_by = serializers.ReadOnlyField(source="posted_by.username")

    class Meta:
        model = JobPost
        fields = (
            "id", "title", "company", "location", "job_type", "description",
            "apply_url", "contact_email", "is_active", "posted_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        # Mirror the model-level rule (DRF doesn't call Model.clean()).
        apply_url = attrs.get("apply_url", getattr(self.instance, "apply_url", ""))
        email = attrs.get("contact_email", getattr(self.instance, "contact_email", ""))
        if not apply_url and not email:
            raise serializers.ValidationError("Provide an application link or a contact email.")
        return attrs


class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source="created_by.username")
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id", "title", "description", "location", "start_at", "end_at",
            "cover_image", "is_upcoming", "created_by", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_at": "The end time must be after the start time."})
        return attrs
