from django.contrib import admin

from apps.accounts.models import SocialIdentity, TravelerProfile


@admin.register(TravelerProfile)
class TravelerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "role",
        "traveler_type",
        "onboarding_completed_at",
        "created_at",
    )
    list_filter = ("role", "traveler_type", "onboarding_completed_at", "created_at")
    search_fields = ("full_name", "user__email", "user__username")
    readonly_fields = (
        "onboarding_completed_at",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("user",)

    @admin.display(description="Email", ordering="user__email")
    def email(self, obj):
        return obj.user.email


@admin.register(SocialIdentity)
class SocialIdentityAdmin(admin.ModelAdmin):
    list_display = ("provider", "provider_email", "user", "created_at")
    list_filter = ("provider", "created_at")
    search_fields = ("subject", "provider_email", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
