"""
Page types.

Every page is a title plus an ordered StreamField of registered sections, so
editors compose any layout without a developer. The API exposes the body as
JSON; the frontend maps each block's `component` to a React component.
"""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.cms.blocks import SECTION_BLOCKS
from apps.core.serializers import serialize_image


class BasePage(Page):
    """Shared SEO/social fields and body StreamField for every Lumora page."""

    # The StreamField is the editable page outline: editors see Hero, Stats,
    # Package grid, FAQ, CTA, etc. in the same order the frontend renders them.
    # Keep the field open so the outline is immediately visible in Wagtail.
    body = StreamField(SECTION_BLOCKS, blank=True, collapsed=False)

    og_image = models.ForeignKey(
        "core.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Social share image",
    )
    canonical_url = models.URLField(blank=True)
    noindex = models.BooleanField(default=False, help_text="Ask search engines not to index this page.")

    content_panels = Page.content_panels + [FieldPanel("body", heading="Page sections")]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel(
            [FieldPanel("og_image"), FieldPanel("canonical_url"), FieldPanel("noindex")],
            heading="SEO & social",
        )
    ]

    search_fields = Page.search_fields + [index.SearchField("body")]

    api_fields = [
        APIField("body"),
        APIField("seo"),
        APIField("last_published_at"),
    ]

    class Meta:
        abstract = True

    @property
    def seo(self):
        return {
            "title": self.seo_title or self.title,
            "description": self.search_description,
            "canonical_url": self.canonical_url or self.get_full_url(),
            "noindex": self.noindex,
            "og_image": serialize_image(self.og_image, ["card", "wide"]),
            "slug": self.slug,
        }


class HomePage(BasePage):
    """The site home page. Only one is expected per site."""

    subpage_types = ["cms.StandardPage", "cms.PackageIndexPage", "cms.BlogIndexPage"]
    parent_page_types = ["wagtailcore.Page"]
    max_count = 1

    class Meta:
        verbose_name = "Home page"


class StandardPage(BasePage):
    """Any composed content page: About, Contact, landing pages…"""

    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body", heading="Page sections")]

    api_fields = BasePage.api_fields + [APIField("intro")]

    class Meta:
        verbose_name = "Standard page"


class PackageIndexPage(BasePage):
    """
    Listing page for packages. The package data itself comes from the catalog
    API; this page provides the editorial framing around it.
    """

    intro = models.TextField(blank=True)
    packages_per_page = models.PositiveIntegerField(default=12)
    show_filters = models.BooleanField(default=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [FieldPanel("packages_per_page"), FieldPanel("show_filters")], heading="Listing options"
        ),
        FieldPanel("body", heading="Page sections"),
    ]

    api_fields = BasePage.api_fields + [
        APIField("intro"),
        APIField("packages_per_page"),
        APIField("show_filters"),
    ]

    subpage_types = ["cms.StandardPage"]

    class Meta:
        verbose_name = "Package index page"


class BlogIndexPage(BasePage):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body", heading="Page sections")]
    api_fields = BasePage.api_fields + [APIField("intro")]
    subpage_types = ["cms.BlogPostPage"]

    class Meta:
        verbose_name = "Blog index page"


class BlogPostPage(BasePage):
    """Travel stories / guides — body uses the same section library."""

    excerpt = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    published_date = models.DateField(null=True, blank=True)
    author_name = models.CharField(max_length=120, blank=True)
    read_time_minutes = models.PositiveIntegerField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("excerpt"),
        FieldPanel("hero_image"),
        MultiFieldPanel(
            [FieldPanel("published_date"), FieldPanel("author_name"), FieldPanel("read_time_minutes")],
            heading="Meta",
        ),
        FieldPanel("body", heading="Page sections"),
    ]

    api_fields = BasePage.api_fields + [
        APIField("excerpt"),
        APIField("hero_image_data"),
        APIField("published_date"),
        APIField("author_name"),
        APIField("read_time_minutes"),
    ]

    parent_page_types = ["cms.BlogIndexPage"]

    class Meta:
        verbose_name = "Blog post"

    @property
    def hero_image_data(self):
        return serialize_image(self.hero_image)
