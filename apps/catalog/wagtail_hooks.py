from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from apps.catalog.models import Package


class PackageViewSet(SnippetViewSet):
    model = Package
    icon = "tag"
    menu_label = "Packages"
    menu_order = 150
    add_to_admin_menu = True
    list_display = ["title", "category", "price", "currency", "is_active", "is_popular"]
    list_filter = ["category", "is_active", "is_popular", "source"]
    search_fields = ["title", "summary"]
    ordering = ["sort_order", "title"]


register_snippet(PackageViewSet)
