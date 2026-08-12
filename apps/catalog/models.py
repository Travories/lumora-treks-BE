"""
Reusable content the editors maintain once and reference from many sections:
travel packages, destinations and testimonials.

Packages can be authored fully in the CMS, or mirrored from the company SDK
(`external_id` + `source`), so a package grid can mix both without the
frontend caring which is which.
"""

from django.db import models
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class SlugMixin(models.Model):
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "item"
            candidate, counter = base, 2
            model = type(self)
            while model.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Destination(index.Indexed, SlugMixin, models.Model):
    """A place — used by the bento grids and the experience section."""

    LAYOUT_CHOICES = [
        ("small", "Small tile"),
        ("tall", "Tall tile"),
        ("wide", "Wide tile"),
        ("large", "Large feature tile"),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    region = models.CharField(max_length=120, blank=True, help_text="e.g. Annapurna, Everest.")
    best_season = models.CharField(max_length=120, blank=True)
    default_layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default="small")
    link_page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    external_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    panels = [
        MultiFieldPanel(
            [FieldPanel("title"), FieldPanel("slug"), FieldPanel("subtitle"), FieldPanel("description")],
            heading="Content",
        ),
        FieldPanel("image"),
        MultiFieldPanel(
            [FieldPanel("region"), FieldPanel("best_season"), FieldPanel("default_layout")],
            heading="Metadata",
        ),
        MultiFieldPanel(
            [FieldPanel("link_page"), FieldPanel("external_url")],
            heading="Link target",
        ),
        MultiFieldPanel([FieldPanel("is_featured"), FieldPanel("sort_order")], heading="Ordering"),
    ]

    search_fields = [
        index.SearchField("title"),
        index.SearchField("description"),
        index.FilterField("region"),
        index.FilterField("is_featured"),
    ]

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    @property
    def href(self):
        if self.link_page_id:
            return self.link_page.get_url() or f"/{self.link_page.slug}/"
        return self.external_url or None


class PackageHighlight(Orderable):
    package = ParentalKey("catalog.Package", related_name="highlights", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, blank=True, help_text="Iconify name.")

    panels = [FieldPanel("text"), FieldPanel("icon")]

    def __str__(self):
        return self.text


class PackageItineraryDay(Orderable):
    package = ParentalKey("catalog.Package", related_name="itinerary", on_delete=models.CASCADE)
    day_label = models.CharField(max_length=60, blank=True, help_text="e.g. Day 1 — defaults to position.")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    panels = [FieldPanel("day_label"), FieldPanel("title"), FieldPanel("description"), FieldPanel("image")]

    def __str__(self):
        return self.title


class PackageGalleryImage(Orderable):
    package = ParentalKey("catalog.Package", related_name="gallery", on_delete=models.CASCADE)
    image = models.ForeignKey("core.CustomImage", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel("image"), FieldPanel("caption")]


class Package(index.Indexed, SlugMixin, ClusterableModel):
    """
    A travel package. Matches the frontend `TravelPackage` type, plus the
    detail-page fields (itinerary, gallery, inclusions).
    """

    SOURCE_CMS = "cms"
    SOURCE_SDK = "sdk"
    SOURCE_CHOICES = [(SOURCE_CMS, "Authored in the CMS"), (SOURCE_SDK, "Mirrored from the Travories SDK")]

    CATEGORY_CHOICES = [
        ("Trekking", "Trekking"),
        ("Sightseeing", "Sightseeing"),
        ("Paragliding", "Paragliding"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(
        max_length=40,
        choices=CATEGORY_CHOICES,
        default="Trekking",
        help_text="Drives the /packages page filter tabs.",
    )
    summary = models.TextField(blank=True, help_text="Short line shown on the card.")
    description = RichTextField(blank=True, features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])
    image = models.ForeignKey(
        "core.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Card / hero image.",
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0)
    duration = models.CharField(max_length=120, blank=True, help_text="e.g. 4 days & 3 nights")
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    people_count = models.PositiveIntegerField(default=1, help_text="Max group size.")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    difficulty = models.CharField(
        max_length=40,
        blank=True,
        choices=[
            ("easy", "Easy"),
            ("moderate", "Moderate"),
            ("challenging", "Challenging"),
            ("strenuous", "Strenuous"),
        ],
    )
    destination = models.ForeignKey(
        "catalog.Destination", null=True, blank=True, on_delete=models.SET_NULL, related_name="packages"
    )
    includes = models.TextField(blank=True, help_text="One item per line.")
    excludes = models.TextField(blank=True, help_text="One item per line.")
    is_popular = models.BooleanField(default=False, help_text="Shown in the Popular Packages carousel.")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_CMS)
    external_id = models.CharField(
        max_length=120,
        blank=True,
        help_text="Package id in the company SDK, when this entry mirrors an SDK package.",
    )
    booking_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("title"), FieldPanel("slug"), FieldPanel("category"), FieldPanel("summary"), FieldPanel("description")],
            heading="Content",
        ),
        FieldPanel("image"),
        InlinePanel("gallery", label="Gallery image"),
        MultiFieldPanel(
            [
                FieldPanel("price"),
                FieldPanel("discount_price"),
                FieldPanel("currency"),
                FieldPanel("duration"),
                FieldPanel("duration_days"),
                FieldPanel("people_count"),
                FieldPanel("difficulty"),
                FieldPanel("rating"),
                FieldPanel("review_count"),
            ],
            heading="Package facts",
        ),
        FieldPanel("destination"),
        InlinePanel("highlights", label="Highlight"),
        InlinePanel("itinerary", label="Itinerary day"),
        MultiFieldPanel([FieldPanel("includes"), FieldPanel("excludes")], heading="Inclusions"),
        MultiFieldPanel(
            [FieldPanel("is_popular"), FieldPanel("is_active"), FieldPanel("sort_order")],
            heading="Visibility",
        ),
        MultiFieldPanel(
            [FieldPanel("source"), FieldPanel("external_id"), FieldPanel("booking_url")],
            heading="Booking / SDK link",
        ),
    ]

    search_fields = [
        index.SearchField("title"),
        index.SearchField("summary"),
        index.AutocompleteField("title"),
        index.FilterField("is_popular"),
        index.FilterField("is_active"),
        index.FilterField("category"),
    ]

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    @property
    def includes_list(self):
        return [line.strip() for line in self.includes.splitlines() if line.strip()]

    @property
    def excludes_list(self):
        return [line.strip() for line in self.excludes.splitlines() if line.strip()]


class Testimonial(index.Indexed, models.Model):
    """A customer review, reusable across testimonial sections."""

    author_name = models.CharField(max_length=120)
    author_role = models.CharField(max_length=160, blank=True, help_text="e.g. Everest Base Camp Trekker")
    quote = models.TextField()
    avatar = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    rating = models.PositiveSmallIntegerField(default=5)
    package = models.ForeignKey(
        "catalog.Package", null=True, blank=True, on_delete=models.SET_NULL, related_name="testimonials"
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    panels = [
        FieldPanel("quote"),
        MultiFieldPanel(
            [FieldPanel("author_name"), FieldPanel("author_role"), FieldPanel("avatar")],
            heading="Author",
        ),
        MultiFieldPanel(
            [FieldPanel("rating"), FieldPanel("package"), FieldPanel("is_featured"), FieldPanel("sort_order")],
            heading="Metadata",
        ),
    ]

    search_fields = [index.SearchField("quote"), index.SearchField("author_name")]

    class Meta:
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return f"{self.author_name} — {self.quote[:40]}"


register_snippet(Destination)
register_snippet(Package)
register_snippet(Testimonial)
