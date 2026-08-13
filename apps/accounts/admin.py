from django.contrib import admin

from apps.accounts.models import TravelerProfile


@admin.register(TravelerProfile)
class TravelerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "traveler_type",
        "onboarding_completed_at",
        "created_at",
    )
    list_filter = ("traveler_type", "onboarding_completed_at", "created_at")
    search_fields = ("full_name", "user__email", "google_sub")
    readonly_fields = (
        "google_sub",
        "onboarding_completed_at",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("user",)

    @admin.display(description="Email", ordering="user__email")
    def email(self, obj):
        return obj.user.email
