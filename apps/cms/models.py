"""
Page types.

Every page is a title plus an ordered StreamField of registered sections, so
editors compose any layout without a developer. The API exposes the body as
JSON; the frontend maps each block's `component` to a React component.
"""

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.catalog.editorial import destination_page_related_items, package_page_related_items
from apps.catalog.serializers import serialize_destination, serialize_package
from apps.cms.blocks import SECTION_BLOCKS, section_blocks
from apps.cms.blocks.article import ARTICLE_BLOCKS
from apps.core.fields import LimitedCharField, LimitedTextField
from apps.core.panels import RelatedLinksPanel
from apps.core.serializers import serialize_image


def page_body(*block_names):
    """Build a compact StreamField containing only this page type's sections."""

    return StreamField(section_blocks(*block_names), blank=True, collapsed=True)


class HeadlessPageMixin:
    """
    Pages are rendered by the Next.js frontend, never by Wagtail templates.

    Page URLs therefore resolve to `FRONTEND_BASE_URL` + the page's path, so
    "View live" in the admin, the API's `html_url`, SEO canonical URLs and
    rich-text page links all point at the public site. The CMS host never
    serves a page, so a host-relative URL is never correct: `get_url` always
    returns the absolute frontend URL.
    """

    # Wagtail's preview panel renders Django templates, which a headless site
    # doesn't have — hide it rather than show "Preview not available".
    preview_modes = []

    def get_url_parts(self, request=None):
        url_parts = super().get_url_parts(request=request)
        if url_parts is None:
            return None
        site_id, _root_url, page_path = url_parts
        serve_prefix = reverse("wagtail_serve", args=[""])
        if page_path.startswith(serve_prefix):
            page_path = "/" + page_path[len(serve_prefix):]
        # Next.js routes have no trailing slash.
        if len(page_path) > 1:
            page_path = page_path.rstrip("/")
        return site_id, settings.FRONTEND_BASE_URL, page_path

    def get_url(self, request=None, current_site=None):
        return self.get_full_url(request=request)

    url = property(get_url)

    def serve(self, request, *args, **kwargs):
        # Old links to the CMS host (e.g. /cms-preview/about/) land on the site.
        return redirect(self.get_full_url(request=request))


class BasePage(HeadlessPageMixin, Page):
    """Shared SEO/social fields and body StreamField for every Lumora page."""

    # The StreamField is the editable page outline: editors see Hero, Stats,
    # Package grid, FAQ, CTA, etc. in the same order the frontend renders them.
    # Keep each section compact so long pages read as an editable outline.
    body = StreamField(SECTION_BLOCKS, blank=True, collapsed=True)

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


def page_edit_handler(content_panels, layout_panels, *additional_tabs, content_heading="Content"):
    """Keep page data separate from the ordered frontend screen outline."""

    return TabbedInterface(
        [
            ObjectList(content_panels, heading=content_heading),
            *additional_tabs,
            ObjectList(layout_panels, heading="Page layout"),
            ObjectList(BasePage.promote_panels, heading="SEO & sharing"),
            ObjectList(Page.settings_panels, heading="Settings"),
        ]
    )


class HomePage(BasePage):
    """The site home page. Only one is expected per site."""

    body = page_body(
        "hero",
        "intro_stats",
        "popular_packages",
        "experience_showcase",
        "why_choose_us",
        "bento_grid",
        "authentic_experiences",
        "faq",
        "cta_banner",
    )

    subpage_types = [
        "cms.StandardPage",
        "cms.ContactPage",
        "cms.PrivacyPage",
        "cms.PackageIndexPage",
        "cms.DestinationIndexPage",
        "cms.BlogIndexPage",
        "cms.EnquiryPage",
        "cms.CheckoutPage",
    ]
    parent_page_types = ["wagtailcore.Page"]
    max_count = 1
    edit_handler = page_edit_handler(
        Page.content_panels,
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    class Meta:
        verbose_name = "Home page"


class StandardPage(BasePage):
    """Any composed content page: About, Contact, landing pages…"""

    # Generic editorial content blocks only. The transaction routes (Enquiry,
    # Checkout, Payment success) and catalog detail pages live in their own
    # dedicated page models, so those blocks are intentionally excluded here.
    body = page_body(
        "page_hero",
        "header_card",
        "destinations_grid",
        "lead_form",
        "rich_text",
        "gallery",
        "video",
        "embed",
        "faq",
        "cta_banner",
        "spacer",
    )

    intro = models.TextField(blank=True)

    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    api_fields = BasePage.api_fields + [APIField("intro")]

    class Meta:
        verbose_name = "Standard page"


class ContactPage(BasePage):
    """The public contact route and its configurable enquiry form."""

    body = page_body("contact_hero", "contact_form", "why_choose_us", "authentic_experiences", "faq")
    intro = models.TextField(blank=True)

    api_fields = BasePage.api_fields + [APIField("intro")]
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    parent_page_types = ["cms.HomePage"]
    subpage_types = []
    max_count = 1

    class Meta:
        verbose_name = "Contact page"


class PrivacyPage(BasePage):
    """Privacy and data-handling information."""

    body = page_body("page_hero", "rich_text", "faq", "cta_banner")
    intro = models.TextField(blank=True)

    api_fields = BasePage.api_fields + [APIField("intro")]
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    parent_page_types = ["cms.HomePage"]
    subpage_types = []
    max_count = 1

    class Meta:
        verbose_name = "Privacy page"


class EnquiryPage(BasePage):
    """The package enquiry route. Editors control the surrounding copy; the
    enquiry form itself is a fixed section that should not be removed."""

    body = page_body("page_hero", "package_enquiry", "cta_banner")
    intro = models.TextField(blank=True)

    api_fields = BasePage.api_fields + [APIField("intro")]
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    parent_page_types = ["cms.HomePage"]
    subpage_types = []
    max_count = 1

    class Meta:
        verbose_name = "Enquiry page"


class CheckoutPage(BasePage):
    """The checkout route. Locked to the checkout section to protect the
    transaction flow; the success page nests beneath it at /checkout/success/."""

    body = page_body("checkout")

    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.PaymentSuccessPage"]
    max_count = 1
    edit_handler = page_edit_handler(
        Page.content_panels,
        [FieldPanel("body", heading="Checkout screen")],
    )

    class Meta:
        verbose_name = "Checkout page"


class PaymentSuccessPage(BasePage):
    """Post-payment confirmation, served at /checkout/success/."""

    body = page_body("payment_success", "cta_banner")

    parent_page_types = ["cms.CheckoutPage"]
    subpage_types = []
    max_count = 1
    edit_handler = page_edit_handler(
        Page.content_panels,
        [FieldPanel("body", heading="Success screen and follow-up")],
    )

    class Meta:
        verbose_name = "Payment success page"


class DestinationIndexPage(BasePage):
    """The CMS parent for all destination detail pages."""

    body = page_body(
        "page_hero",
        "destinations_grid",
        "experience_showcase",
        "cta_banner",
    )
    intro = models.TextField(blank=True)

    api_fields = BasePage.api_fields + [APIField("intro")]

    subpage_types = ["cms.DestinationDetailPage"]
    parent_page_types = ["cms.HomePage"]
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    class Meta:
        verbose_name = "Destination index page"


class DestinationDetailPage(BasePage):
    """One editable, SEO-capable Wagtail page per catalog destination."""

    body = page_body(
        "destination_header",
        "destination_overview",
        "destination_packages",
        "cta_banner",
    )

    destination = models.OneToOneField(
        "catalog.Destination", on_delete=models.PROTECT, related_name="detail_page"
    )
    api_fields = BasePage.api_fields + [APIField("destination_id"), APIField("destination_data")]
    parent_page_types = ["cms.DestinationIndexPage"]
    edit_handler = page_edit_handler(
        [RelatedLinksPanel(destination_page_related_items, heading="Related content")]
        + Page.content_panels
        + [FieldPanel("destination")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    class Meta:
        verbose_name = "Destination detail page"

    @property
    def destination_data(self):
        return serialize_destination(self.destination, detail=True)


class PackageFolderPage(HeadlessPageMixin, Page):
    """Structural URL segment: `/packages/<package-slug>/`.

    Created automatically with each package (see apps/catalog/signals.py);
    editors work on the package detail page inside it.
    """

    parent_page_types = ["cms.PackageIndexPage"]
    subpage_types = ["cms.PackageDetailPage"]

    class Meta:
        verbose_name = "Package URL folder"


class PackageDetailPage(BasePage):
    """One editable, SEO-capable Wagtail page per catalog package."""

    body = page_body(
        "package_header",
        "package_overview",
        "package_booking",
        "package_itinerary",
        "package_reviews",
        "cta_banner",
    )

    package = models.OneToOneField(
        "catalog.Package", on_delete=models.PROTECT, related_name="detail_page"
    )
    api_fields = BasePage.api_fields + [APIField("package_id"), APIField("package_data")]
    parent_page_types = ["cms.PackageFolderPage"]
    edit_handler = page_edit_handler(
        [RelatedLinksPanel(package_page_related_items, heading="Related content")]
        + Page.content_panels
        + [FieldPanel("package")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    class Meta:
        verbose_name = "Package detail page"

    @property
    def package_data(self):
        return serialize_package(self.package, detail=True)


class PackageIndexPage(BasePage):
    """
    Listing page for packages. The package data itself comes from the catalog
    API; this page provides the editorial framing around it.
    """

    body = page_body("page_hero", "package_listing", "cultural_tours", "cta_banner")
    intro = models.TextField(blank=True)
    packages_per_page = models.PositiveIntegerField(default=12)
    show_filters = models.BooleanField(default=True)

    api_fields = BasePage.api_fields + [
        APIField("intro"),
        APIField("packages_per_page"),
        APIField("show_filters"),
    ]

    subpage_types = ["cms.PackageFolderPage"]
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
        ObjectList(
            [FieldPanel("packages_per_page"), FieldPanel("show_filters")],
            heading="Listing options",
        ),
    )

    class Meta:
        verbose_name = "Package index page"


class BlogIndexPage(BasePage):
    body = page_body("page_hero", "blog_listing", "cta_banner")
    intro = models.TextField(blank=True)

    api_fields = BasePage.api_fields + [APIField("intro")]
    subpage_types = ["cms.BlogPostPage"]
    # Blog post slugs are only unique per parent; the API looks posts up by slug.
    max_count = 1
    edit_handler = page_edit_handler(
        Page.content_panels + [FieldPanel("intro")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
    )

    class Meta:
        verbose_name = "Blog index page"


#: Blog categories — kept in sync with the frontend FilterTabs (`BLOG_CATEGORIES`).
BLOG_CATEGORY_CHOICES = [
    ("Trekking", "Trekking"),
    ("Culture", "Culture"),
    ("Food & Stays", "Food & Stays"),
    ("Guides", "Guides"),
]


class BlogPostPageForm(WagtailAdminPageForm):
    """Story titles appear on cards and the article hero, so they get a UI limit
    like other editorial text (Page.title itself is shared by every page type)."""

    TITLE_MAX_LENGTH = 45

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        title = self.fields["title"]
        title.max_length = self.TITLE_MAX_LENGTH
        title.widget.attrs["maxlength"] = self.TITLE_MAX_LENGTH
        title.validators.append(MaxLengthValidator(self.TITLE_MAX_LENGTH))


class BlogPostPage(BasePage):
    """Travel stories / guides.

    The reading experience is driven by `article_body` — a prose StreamField
    (heading / rich paragraph / pull-quote / image) that the frontend's
    `ArticleBody` renders in a narrow measure. The inherited section `body`
    stays available for any extra full-width sections below the article.
    """

    body = page_body(
        "blog_article_header",
        "blog_article_body",
        "blog_related_stories",
        "cta_banner",
    )
    excerpt = LimitedTextField(blank=True, ui_max_length=125)
    hero_image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    category = models.CharField(max_length=40, blank=True, choices=BLOG_CATEGORY_CHOICES)
    featured = models.BooleanField(
        default=False, help_text="Show as the large featured story at the top of the blog index."
    )
    published_date = models.DateField(null=True, blank=True)
    author_name = LimitedCharField(max_length=120, blank=True, ui_max_length=15)
    author_role = LimitedCharField(max_length=160, blank=True, help_text="e.g. Lead Guide, Travel Writer.", ui_max_length=15)
    author_avatar = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    read_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    article_body = StreamField(ARTICLE_BLOCKS, blank=True, collapsed=False, verbose_name="Article")

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
    base_form_class = BlogPostPageForm
    edit_handler = page_edit_handler(
        Page.content_panels
        + [FieldPanel("excerpt"), FieldPanel("hero_image"), FieldPanel("article_body")],
        [FieldPanel("body", heading="Screen sections — top to bottom")],
        ObjectList(
            [
                FieldPanel("category"),
                FieldPanel("featured"),
                FieldPanel("published_date"),
                FieldPanel("author_name"),
                FieldPanel("author_role"),
                FieldPanel("author_avatar"),
                FieldPanel("read_time_minutes"),
            ],
            heading="Publishing details",
        ),
        content_heading="Story",
    )

    class Meta:
        verbose_name = "Blog post"

    @property
    def hero_image_data(self):
        return serialize_image(self.hero_image)

    @property
    def author_avatar_data(self):
        return serialize_image(self.author_avatar)
