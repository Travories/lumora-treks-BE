from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from apps.leads.models import LeadSubmission


class LeadSubmissionViewSet(SnippetViewSet):
    model = LeadSubmission
    icon = "mail"
    menu_label = "Leads"
    menu_order = 150
    add_to_admin_menu = True
    list_display = [
        "__str__",
        "email",
        "phone",
        Column("package", label="Package", sort_key="package__title"),
        "status",
        DateColumn("submitted_at", label="Received", sort_key="submitted_at"),
    ]
    list_filter = ["status", "form_key", "package"]
    list_export = ["name", "email", "phone", "form_key", "package", "status", "message", "submitted_at"]
    # Small table: ORM search keeps new submissions findable immediately.
    search_backend_name = None
    search_fields = ["name", "email", "phone", "message"]
    ordering = ["-submitted_at"]
    list_per_page = 50
    # Leads arrive from the website forms; editors triage them, not create them.
    copy_view_enabled = False

    def get_queryset(self, request):
        return LeadSubmission.objects.select_related("package")


register_snippet(LeadSubmissionViewSet)
