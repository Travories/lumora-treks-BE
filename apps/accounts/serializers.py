from rest_framework import serializers

from apps.accounts.models import TravelerProfile


class TravelerProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    onboarding_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = TravelerProfile
        fields = (
            "id",
            "email",
            "full_name",
            "avatar_url",
            "interests",
            "traveler_type",
            "onboarding_complete",
        )
        read_only_fields = fields


class GoogleCredentialSerializer(serializers.Serializer):
    credential = serializers.CharField(trim_whitespace=True, max_length=4096)


class OnboardingSerializer(serializers.Serializer):
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
