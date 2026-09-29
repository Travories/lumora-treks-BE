"""
Lumora Admin shell: sidebar structure, branding assets and dashboard.

Sidebar, top to bottom:

    Pages · Blog · Packages · Destinations · Testimonials · Leads   (content)
    Media › Images, Videos, Documents
    Site settings › Brand & contact, Navigation, Footer, Theme, Integrations
    Reports · Administration (users, groups, sites, redirects…) · Help

Content sections register their own menu items (catalog, cms, leads apps);
this module groups the rest and removes Wagtail's generic "Snippets" menu,
since every snippet type now has a named entry of its own.
"""

from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.menu import Menu, SubmenuMenuItem
from wagtail.admin.site_summary import SummaryItem
from wagtail.admin.ui.components import Component
from wagtail.admin.ui.tables import Column
from wagtail.documents.wagtail_hooks import DocumentsMenuItem
from wagtail.images.wagtail_hooks import ImagesMenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from apps.core.models import Video

# ---------------------------------------------------------------------------
# Media: Images, Videos and Documents in one group
# ---------------------------------------------------------------------------

media_menu = Menu(
    register_hook_name="register_media_menu_item",
    construct_hook_name="construct_media_menu",
)


@hooks.register("register_media_menu_item")
def register_images_menu_item():
    return ImagesMenuItem("Images", reverse("wagtailimages:index"), name="images", icon_name="image", order=100)


@hooks.register("register_media_menu_item")
def register_documents_menu_item():
    return DocumentsMenuItem(
        "Documents", reverse("wagtaildocs:index"), name="documents", icon_name="doc-full-inverse", order=300
    )


class VideoViewSet(SnippetViewSet):
    model = Video
    icon = "media"
    menu_label = "Videos"
    menu_order = 200
    menu_hook = "register_media_menu_item"
    list_display = ["title", Column("source", label="Source"), "caption", "created_at"]
    search_backend_name = None
    search_fields = ["title", "caption"]
    ordering = ["-created_at"]


register_snippet(VideoViewSet)


@hooks.register("register_admin_menu_item")
def register_media_menu():
    return SubmenuMenuItem("Media", media_menu, name="media", icon_name="image", order=300)


# ---------------------------------------------------------------------------
# Main menu: drop the duplicates, give Wagtail's settings a clearer name
# ---------------------------------------------------------------------------

# Images/Documents live under Media; every snippet type has its own entry.
_REPLACED_MENU_ITEMS = {"images", "documents", "snippets"}


@hooks.register("construct_main_menu")
def organise_main_menu(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name not in _REPLACED_MENU_ITEMS]
    for item in menu_items:
        if item.name == "settings":
            # Editorial settings moved to "Site settings"; what remains is
            # users, groups, sites, collections, redirects and workflows.
            item.label = "Administration"


@hooks.register("construct_help_menu")
def remove_wagtail_release_notes(request, menu_items):
    menu_items[:] = [item for item in menu_items if not item.name.startswith("whats-new-in-wagtail")]


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------


@hooks.register("insert_global_admin_css")
def lumora_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static("lumora_admin/admin.css"))


@hooks.register("insert_global_admin_js")
def lumora_admin_js():
    return format_html('<script src="{}" defer></script>', static("lumora_admin/char-count.js"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class CountSummaryItem(SummaryItem):
    """A dashboard summary tile: an icon, a count and a link."""

    template_name = "core/home/summary_item.html"

    def __init__(self, request, *, label, icon, url, queryset, order):
        super().__init__(request)
        self.label, self.icon, self.url, self.queryset, self.order = label, icon, url, queryset, order

    def get_context_data(self, parent_context):
        return {"label": self.label, "icon": self.icon, "url": self.url, "count": self.queryset.count()}


def _snippet_url(model, view, request, action="change"):
    viewset = model.snippet_viewset
    if not viewset.permission_policy.user_has_permission(request.user, action):
        return None
    return reverse(viewset.get_url_name(view))


@hooks.register("construct_homepage_summary_items")
def add_content_summary_items(request, summary_items):
    from apps.catalog.models import Destination, Package
    from apps.cms.models import BlogPostPage
    from apps.cms.wagtail_hooks import blog_listing_viewset
    from apps.leads.models import LeadSubmission

    candidates = [
        ("Blog posts", "doc-full", reverse(blog_listing_viewset.get_url_name("index")), BlogPostPage.objects.all(), 110),
        ("Packages", "tag", _snippet_url(Package, "list", request), Package.objects.all(), 120),
        ("Destinations", "globe", _snippet_url(Destination, "list", request), Destination.objects.all(), 130),
    ]
    leads_url = _snippet_url(LeadSubmission, "list", request)
    if leads_url:
        candidates.append(
            ("New leads", "mail", f"{leads_url}?status=new", LeadSubmission.objects.filter(status="new"), 140)
        )
    summary_items.extend(
        CountSummaryItem(request, label=label, icon=icon, url=url, queryset=queryset, order=order)
        for label, icon, url, queryset, order in candidates
        if url
    )


class QuickActionsPanel(Component):
    """The everyday editorial starting points, one click from the dashboard."""

    name = "quick_actions"
    order = 50
    template_name = "core/home/quick_actions.html"

    def __init__(self, actions):
        self.actions = actions

    def get_context_data(self, parent_context):
        return {"actions": self.actions}


@hooks.register("construct_homepage_panels")
def add_quick_actions_panel(request, panels):
    from apps.catalog.models import Destination, Package
    from apps.cms.models import BlogIndexPage
    from apps.leads.models import LeadSubmission

    actions = []
    blog_index = BlogIndexPage.objects.live().first()
    if blog_index and blog_index.permissions_for_user(request.user).can_add_subpage():
        actions.append(
            ("Write a blog post", "doc-full", reverse("wagtailadmin_pages:add", args=("cms", "blogpostpage", blog_index.pk)))
        )
    for label, icon, model in (("Add a package", "tag", Package), ("Add a destination", "globe", Destination)):
        url = _snippet_url(model, "add", request, action="add")
        if url:
            actions.append((label, icon, url))
    leads_url = _snippet_url(LeadSubmission, "list", request)
    if leads_url:
        actions.append(("Review new leads", "mail", f"{leads_url}?status=new"))

    if actions:
        panels.append(QuickActionsPanel(actions))
