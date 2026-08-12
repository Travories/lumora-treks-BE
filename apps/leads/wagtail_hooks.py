from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from apps.leads.models import LeadSubmission


class LeadSubmissionViewSet(SnippetViewSet):
    model = LeadSubmission
    icon = "mail"
    menu_label = "Leads"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["name", "email", "form_key", "status", "submitted_at"]
    list_filter = ["form_key", "status"]
    search_fields = ["name", "email", "phone", "message"]
    ordering = ["-submitted_at"]


register_snippet(LeadSubmissionViewSet)
