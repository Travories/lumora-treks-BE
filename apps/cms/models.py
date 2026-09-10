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
from apps.cms.blocks.article import ARTICLE_BLOCKS
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

    subpage_types = [
        "cms.StandardPage",
        "cms.PackageIndexPage",
        "cms.DestinationIndexPage",
        "cms.BlogIndexPage",
    ]
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


class DestinationIndexPage(BasePage):
    """The CMS parent for all destination detail pages."""

    subpage_types = ["cms.DestinationDetailPage"]
    parent_page_types = ["cms.HomePage"]

    class Meta:
        verbose_name = "Destination index page"


class DestinationDetailPage(BasePage):
    """One editable, SEO-capable Wagtail page per catalog destination."""

    destination = models.OneToOneField(
        "catalog.Destination", on_delete=models.PROTECT, related_name="detail_page"
    )
    content_panels = Page.content_panels + [FieldPanel("destination"), FieldPanel("body", heading="Page sections")]
    api_fields = BasePage.api_fields + [APIField("destination_id")]
    parent_page_types = ["cms.DestinationIndexPage"]

    class Meta:
        verbose_name = "Destination detail page"


class PackageFolderPage(Page):
    """Structural URL segment: `/packages/<package-slug>/`."""

    parent_page_types = ["cms.PackageIndexPage"]
    subpage_types = ["cms.PackageDetailPage"]

    class Meta:
        verbose_name = "Package URL folder"


class PackageDetailPage(BasePage):
    """One editable, SEO-capable Wagtail page per catalog package."""

    package = models.OneToOneField(
        "catalog.Package", on_delete=models.PROTECT, related_name="detail_page"
    )
    content_panels = Page.content_panels + [FieldPanel("package"), FieldPanel("body", heading="Page sections")]
    api_fields = BasePage.api_fields + [APIField("package_id")]
    parent_page_types = ["cms.PackageFolderPage"]

    class Meta:
        verbose_name = "Package detail page"


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

    subpage_types = ["cms.PackageFolderPage"]

    class Meta:
        verbose_name = "Package index page"


class BlogIndexPage(BasePage):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body", heading="Page sections")]
    api_fields = BasePage.api_fields + [APIField("intro")]
    subpage_types = ["cms.BlogPostPage"]

    class Meta:
        verbose_name = "Blog index page"


#: Blog categories — kept in sync with the frontend FilterTabs (`BLOG_CATEGORIES`).
BLOG_CATEGORY_CHOICES = [
    ("Trekking", "Trekking"),
    ("Culture", "Culture"),
    ("Food & Stays", "Food & Stays"),
    ("Guides", "Guides"),
]


class BlogPostPage(BasePage):
    """Travel stories / guides.

    The reading experience is driven by `article_body` — a prose StreamField
    (heading / rich paragraph / pull-quote / image) that the frontend's
    `ArticleBody` renders in a narrow measure. The inherited section `body`
    stays available for any extra full-width sections below the article.
    """

    excerpt = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    category = models.CharField(max_length=40, blank=True, choices=BLOG_CATEGORY_CHOICES)
    featured = models.BooleanField(
        default=False, help_text="Show as the large featured story at the top of the blog index."
    )
    published_date = models.DateField(null=True, blank=True)
    author_name = models.CharField(max_length=120, blank=True)
    author_role = models.CharField(max_length=160, blank=True, help_text="e.g. Lead Guide, Travel Writer.")
    author_avatar = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    read_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    article_body = StreamField(ARTICLE_BLOCKS, blank=True, collapsed=False, verbose_name="Article")

    content_panels = Page.content_panels + [
        FieldPanel("excerpt"),
        FieldPanel("hero_image"),
        MultiFieldPanel(
            [FieldPanel("category"), FieldPanel("featured")],
            heading="Classification",
        ),
        MultiFieldPanel(
            [
                FieldPanel("published_date"),
                FieldPanel("author_name"),
                FieldPanel("author_role"),
                FieldPanel("author_avatar"),
                FieldPanel("read_time_minutes"),
            ],
            heading="Meta",
        ),
        FieldPanel("article_body"),
        FieldPanel("body", heading="Extra sections"),
    ]

    api_fields = BasePage.api_fields + [
        APIField("excerpt"),
        APIField("hero_image_data"),
        APIField("category"),
        APIField("featured"),
        APIField("published_date"),
        APIField("author_name"),
        APIField("author_role"),
        APIField("author_avatar_data"),
        APIField("read_time_minutes"),
        APIField("article_body"),
    ]

    parent_page_types = ["cms.BlogIndexPage"]

    class Meta:
        verbose_name = "Blog post"

    @property
    def hero_image_data(self):
        return serialize_image(self.hero_image)

    @property
    def author_avatar_data(self):
        return serialize_image(self.author_avatar)
