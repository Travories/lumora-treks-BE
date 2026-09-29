from django.db.models import Count
from django.urls import reverse
from wagtail import hooks
from wagtail.admin.ui.tables import BooleanColumn, Column
from wagtail.admin.widgets import Button
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from apps.catalog.editorial import detail_page_for
from apps.catalog.models import Destination, Package, Testimonial

# Catalog listings are small (dozens of rows), so search with the ORM rather
# than the Wagtail search index: results are always current without
# `update_index`, and related fields (destination name) are searchable.


class PackageViewSet(SnippetViewSet):
    model = Package
    icon = "tag"
    menu_label = "Packages"
    menu_order = 120
    add_to_admin_menu = True
    list_display = [
        "title",
        Column("destination", label="Destination", sort_key="destination__title"),
        "category",
        Column("price_label", label="Price", sort_key="price"),
        "duration",
        BooleanColumn("is_active", label="Active", sort_key="is_active"),
        BooleanColumn("is_popular", label="Popular", sort_key="is_popular"),
    ]
    list_filter = ["destination", "category", "difficulty", "is_active", "is_popular", "source"]
    list_export = ["title", "public_code", "destination", "category", "price", "currency", "duration", "is_active"]
    search_backend_name = None
    search_fields = ["title", "summary", "public_code", "destination__title"]
    ordering = ["sort_order", "title"]
    list_per_page = 50

    def get_queryset(self, request):
        return Package.objects.select_related("destination")


class DestinationViewSet(SnippetViewSet):
    model = Destination
    icon = "globe"
    menu_label = "Destinations"
    menu_order = 130
    add_to_admin_menu = True
    list_display = [
        "title",
        "region",
        Column("package_count", label="Packages", sort_key="package_count"),
        BooleanColumn("is_featured", label="Featured", sort_key="is_featured"),
    ]
    list_filter = ["region", "is_featured"]
    search_backend_name = None
    search_fields = ["title", "subtitle", "region"]
    ordering = ["sort_order", "title"]
    list_per_page = 50

    def get_queryset(self, request):
        return Destination.objects.annotate(package_count=Count("packages"))


class TestimonialViewSet(SnippetViewSet):
    model = Testimonial
    icon = "openquote"
    menu_label = "Testimonials"
    menu_order = 140
    add_to_admin_menu = True
    list_display = [
        "author_name",
        "author_role",
        Column("package", label="Package", sort_key="package__title"),
        "rating",
        BooleanColumn("is_featured", label="Featured", sort_key="is_featured"),
    ]
    list_filter = ["package", "rating", "is_featured"]
    search_backend_name = None
    search_fields = ["author_name", "author_role", "quote", "package__title"]
    ordering = ["sort_order", "-id"]

    def get_queryset(self, request):
        return Testimonial.objects.select_related("package")


register_snippet(PackageViewSet)
register_snippet(DestinationViewSet)
register_snippet(TestimonialViewSet)


@hooks.register("register_snippet_listing_buttons")
def catalog_page_listing_buttons(snippet, user, next_url=None):
    """Row "More" actions on Packages / Destinations to jump to the public page."""

    if not isinstance(snippet, (Package, Destination)):
        return []
    page = detail_page_for(snippet)
    if page is None:
        return []

    buttons = []
    if page.permissions_for_user(user).can_edit():
        buttons.append(
            Button(
                "Edit page sections & SEO",
                reverse("wagtailadmin_pages:edit", args=[page.pk]),
                icon_name="doc-empty-inverse",
                priority=20,
            )
        )
    if page.live and getattr(snippet, "is_active", True):
        buttons.append(
            Button(
                "View on site",
                page.full_url,
                icon_name="link-external",
                attrs={"target": "_blank", "rel": "noopener"},
                priority=30,
            )
        )
    return buttons

