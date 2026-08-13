from rest_framework import serializers

from apps.accounts.models import TravelerProfile


class RejectUnknownFieldsSerializer(serializers.Serializer):
    """Reject fields outside an endpoint's explicit writable contract."""

    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown_fields = set(data.keys()) - set(self.fields)
            if unknown_fields:
                raise serializers.ValidationError(
                    {
                        field: ["This field is not accepted by this endpoint."]
                        for field in sorted(unknown_fields)
                    }
                )
        return super().to_internal_value(data)


class TravelerProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    onboarding_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = TravelerProfile
        fields = (
            "id",
            "email",
            "role",
            "full_name",
            "interests",
            "traveler_type",
            "onboarding_complete",
        )
        read_only_fields = fields


class GoogleCredentialSerializer(RejectUnknownFieldsSerializer):
    credential = serializers.CharField(trim_whitespace=True, max_length=4096)


class OnboardingSerializer(RejectUnknownFieldsSerializer):
    full_name = serializers.CharField(
        required=False,
        min_length=2,
        max_length=150,
        trim_whitespace=True,
    )
    interests = serializers.ListField(
        child=serializers.ChoiceField(choices=TravelerProfile.INTEREST_CHOICES),
        required=False,
        allow_empty=False,
        max_length=TravelerProfile.MAX_INTERESTS,
    )
    traveler_type = serializers.ChoiceField(
        choices=TravelerProfile.TRAVELER_TYPE_CHOICES,
        required=False,
    )

    def validate_interests(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Choose each interest only once.")
        return value

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one onboarding field.")
        return attrs
