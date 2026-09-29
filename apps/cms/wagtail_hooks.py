from wagtail import hooks
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.viewsets.pages import PageListingViewSet

from apps.cms.models import BlogPostPage

_PAGE_COLUMNS = {column.name: column for column in PageListingViewSet.index_view_class.base_columns}


class BlogListingViewSet(PageListingViewSet):
    """Every blog post in one flat, searchable list — no page-tree digging."""

    model = BlogPostPage
    icon = "doc-full"
    menu_label = "Blog"
    menu_order = 110
    add_to_admin_menu = True
    name = "blog"
    columns = [
        _PAGE_COLUMNS["bulk_actions"],
        _PAGE_COLUMNS["title"],
        Column("category", label="Category", sort_key="category", width="12%"),
        Column("author_name", label="Author", sort_key="author_name", width="14%"),
        DateColumn("published_date", label="Published", sort_key="published_date", width="12%"),
        _PAGE_COLUMNS["latest_revision_created_at"],
        _PAGE_COLUMNS["status"],
    ]
    list_filter = ["category", "featured"]


blog_listing_viewset = BlogListingViewSet()


@hooks.register("register_admin_viewset")
def register_blog_listing():
    return blog_listing_viewset
