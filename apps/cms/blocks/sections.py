"""
The Lumora section library.

Every block here is the CMS counterpart of a React component in
`lumora-treks-FE/src/components`. `component` is the contract: the API emits it
on every block and the frontend's block registry maps it to the component.

    apps/cms/blocks/sections.py          src/components/sections/*.tsx
    ─────────────────────────────        ──────────────────────────────
    HeroBlock            component="Hero"            → Hero.tsx
    IntroStatsBlock      component="IntroStats"      → IntroStats.tsx
    ...
"""

from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from apps.catalog.serializers import (
    serialize_destination,
    serialize_package,
    serialize_testimonial,
)
from apps.core.blocks import (
    APIImageChooserBlock,
    APIRichTextBlock,
    ButtonBlock,
    HeadingGroupBlock,
    IconBlock,
    LinkBlock,
    SectionBlock,
    VideoChooserBlock,
    APIEmbedBlock,
)

# ---------------------------------------------------------------------------
# Snippet choosers that serialize to full objects
# ---------------------------------------------------------------------------


class PackageChooserBlock(SnippetChooserBlock):
    def __init__(self, **kwargs):
        super().__init__("catalog.Package", **kwargs)

    def get_api_representation(self, value, context=None):
        return serialize_package(value)


class PackageDetailChooserBlock(PackageChooserBlock):
    def get_api_representation(self, value, context=None):
        return serialize_package(value, detail=True)


class DestinationChooserBlock(SnippetChooserBlock):
    def __init__(self, **kwargs):
        super().__init__("catalog.Destination", **kwargs)

    def get_api_representation(self, value, context=None):
        return serialize_destination(value)


class DestinationDetailChooserBlock(DestinationChooserBlock):
    def get_api_representation(self, value, context=None):
        return serialize_destination(value, detail=True)


class TestimonialChooserBlock(SnippetChooserBlock):
    def __init__(self, **kwargs):
        super().__init__("catalog.Testimonial", **kwargs)

    def get_api_representation(self, value, context=None):
        return serialize_testimonial(value)


# ---------------------------------------------------------------------------
# Small building blocks reused by several sections
# ---------------------------------------------------------------------------


class StatBlock(blocks.StructBlock):
    value = blocks.CharBlock(max_length=20, help_text="e.g. 24K+, 4.9, 120")
    label = blocks.CharBlock(max_length=80)
    icon = IconBlock()

    class Meta:
        icon = "form"
        label = "Stat"


class MediaBlock(blocks.StructBlock):
    """Image or video in one field — used anywhere a section accepts either."""

    media_type = blocks.ChoiceBlock(
        choices=[("image", "Image"), ("video", "Video"), ("embed", "Embed (YouTube/Vimeo)")],
        default="image",
    )
    image = APIImageChooserBlock(required=False)
    video = VideoChooserBlock(required=False)
    embed = APIEmbedBlock(required=False)
    alt_override = blocks.CharBlock(required=False, max_length=255)

    class Meta:
        icon = "image"
        label = "Media"


class DestinationCardBlock(blocks.StructBlock):
    """
    Mirrors `components/ui/DestinationCard.tsx`. Either reference a Destination
    snippet (recommended) or type a one-off card inline.
    """

    destination = DestinationChooserBlock(
        required=False, help_text="Pick from the destination library, or fill the fields below."
    )
    title = blocks.CharBlock(required=False, max_length=200)
    description = blocks.TextBlock(required=False)
    image = APIImageChooserBlock(required=False)
    variant = blocks.ChoiceBlock(
        choices=[
            ("default", "Default"),
            ("big-package", "Big package"),
            ("package-card", "Package card (with arrow)"),
        ],
        default="default",
    )
    layout = blocks.ChoiceBlock(
        choices=[
            ("small", "Small tile"),
            ("tall", "Tall tile"),
            ("wide", "Wide tile"),
            ("large", "Large feature tile"),
        ],
        default="small",
        help_text="Grid footprint inside bento layouts.",
    )
    link = LinkBlock(required=False)

    class Meta:
        icon = "image"
        label = "Destination card"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        destination = data.get("destination") or {}
        # Inline values win; otherwise fall back to the chosen snippet.
        data["title"] = data.get("title") or destination.get("title") or ""
        data["image"] = data.get("image") or destination.get("image")
        data["href"] = (data.get("link") or {}).get("href") or destination.get("href")
        return data


# ---------------------------------------------------------------------------
# Registered sections — one per frontend component
# ---------------------------------------------------------------------------


class HeroSlideBlock(blocks.StructBlock):
    image = APIImageChooserBlock(required=False)
    video = VideoChooserBlock(required=False, help_text="Optional background video, overrides the image.")
    alt = blocks.CharBlock(required=False, max_length=200)
    heading_override = blocks.CharBlock(
        required=False, max_length=200, help_text="Per-slide heading; falls back to the hero heading."
    )

    class Meta:
        icon = "image"
        label = "Slide"


class HeroBlock(SectionBlock):
    """→ `src/components/sections/Hero.tsx`"""

    component = "Hero"

    heading = blocks.CharBlock(max_length=200, default="Travel beyond destinations")
    subheading = blocks.TextBlock(required=False)
    slides = blocks.ListBlock(HeroSlideBlock(), min_num=1, label="Slides")
    mountain_cutout = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Clip a copy of the slide into a skyline in front of the heading.",
    )
    show_search = blocks.BooleanBlock(required=False, default=True, label="Show search bar")
    search_location_label = blocks.CharBlock(required=False, default="Location", max_length=60)
    search_location_placeholder = blocks.CharBlock(required=False, default="Where to go?", max_length=80)
    search_date_label = blocks.CharBlock(required=False, default="Date", max_length=60)
    search_date_placeholder = blocks.CharBlock(required=False, default="Add dates", max_length=80)
    search_button_label = blocks.CharBlock(required=False, default="Search", max_length=40)
    buttons = blocks.ListBlock(ButtonBlock(), required=False, default=[], label="Call to action buttons")

    class Meta:
        icon = "image"
        label = "Hero"
        group = "Sections"


class HeaderCardBlock(SectionBlock):
    """→ smaller inner-page banner. Frontend: `HeaderCard.tsx`"""

    component = "HeaderCard"

    heading = HeadingGroupBlock()
    image = APIImageChooserBlock(required=False)
    buttons = blocks.ListBlock(ButtonBlock(), required=False, default=[])
    overlay_opacity = blocks.IntegerBlock(default=60, min_value=0, max_value=100)

    class Meta:
        icon = "doc-full"
        label = "Header card"
        group = "Sections"


class SocialLinkBlock(blocks.StructBlock):
    """One social icon + link, used by `ContactFormBlock.socials`."""

    icon = IconBlock(help_text="Iconify glyph, e.g. mdi:facebook")
    label = blocks.CharBlock(max_length=40)
    url = blocks.URLBlock(required=False)

    class Meta:
        icon = "link"


class ContactHeroBlock(SectionBlock):
    """→ `src/components/sections/ContactHero.tsx` — editorial hero for /contact (Figma 75:646)."""

    component = "ContactHero"

    heading = blocks.CharBlock(max_length=100, default="Create Memories")
    subtitle = blocks.CharBlock(
        max_length=300,
        default="Mountains, forests, heritage sites, and hidden gems are just the beginning of your next adventure.",
    )
    subtitle_highlight = blocks.CharBlock(
        required=False, max_length=200, default="just the beginning of your next adventure."
    )
    tagline = blocks.CharBlock(max_length=200, default="Travel is more than a destination.")
    tagline_highlight = blocks.CharBlock(required=False, max_length=50, default="Travel")
    closing_heading = blocks.CharBlock(max_length=100, default="beyond maps")
    closing_text = blocks.CharBlock(
        max_length=300,
        default="We design meaningful travel experiences that connect you with nature, culture, and unforgettable journey at a time.",
    )
    closing_text_highlight = blocks.CharBlock(
        required=False, max_length=200, default="and unforgettable journey at a time."
    )
    image = APIImageChooserBlock()

    class Meta:
        icon = "image"
        label = "Contact hero"
        group = "Sections"


class ContactFormBlock(SectionBlock):
    """→ `src/components/sections/ContactForm.tsx` (Figma 75:690) — posts to
    `/api/v2/leads/` with `form_key="contact"`."""

    component = "ContactForm"

    heading = blocks.CharBlock(max_length=200, default="Don't Hesitate to Contact Us")
    heading_highlight = blocks.CharBlock(required=False, max_length=100, default="Contact Us")
    description = blocks.TextBlock(
        required=False,
        default="Whether you have a quick question or want to book a full consultation — "
        "we're easy to reach. Fill in the form and we'll respond within one business day",
    )
    description_highlight = blocks.CharBlock(
        required=False, max_length=200, default="Fill in the form and we'll respond within one business day"
    )
    socials = blocks.ListBlock(SocialLinkBlock(), required=False, default=[])
    destinations = blocks.ListBlock(DestinationChooserBlock(), required=False, default=[])
    submit_label = blocks.CharBlock(required=False, max_length=40, default="Reserve Now")

    class Meta:
        icon = "form"
        label = "Contact form"
        group = "Sections"


class PageHeroBlock(SectionBlock):
    """→ `src/components/sections/PageHero.tsx` for listing and landing pages."""

    component = "PageHero"

    title = blocks.CharBlock(max_length=200)
    subtitle = blocks.TextBlock(required=False)
    image = APIImageChooserBlock()
    image_alt = blocks.CharBlock(required=False, max_length=200)
    image_width = blocks.IntegerBlock(default=565, min_value=100, max_value=1600)
    image_height = blocks.IntegerBlock(default=457, min_value=100, max_value=1600)
    show_search = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "image"
        label = "Page hero"
        group = "Sections"


class IntroStatsBlock(SectionBlock):
    """→ `src/components/sections/IntroStats.tsx`"""

    component = "IntroStats"

    heading = blocks.TextBlock(help_text="Large centred statement.")
    highlight = blocks.CharBlock(
        required=False,
        max_length=120,
        help_text="Words inside the heading to render in brand green italics.",
    )
    description = blocks.TextBlock(required=False)
    description_highlight = blocks.CharBlock(required=False, max_length=200)
    stats = blocks.ListBlock(StatBlock(), min_num=1, max_num=6)

    class Meta:
        icon = "form"
        label = "Intro + stats"
        group = "Sections"


class PopularPackagesBlock(SectionBlock):
    """→ `src/components/sections/PopularPackages.tsx` (carousel of PackageCard)"""

    component = "PopularPackages"

    heading = HeadingGroupBlock()
    source = blocks.ChoiceBlock(
        choices=[
            ("popular", "Automatic — packages flagged 'popular'"),
            ("selected", "Hand-picked packages"),
            ("destination", "All packages for a destination"),
            ("sdk", "Company SDK ids (fetched by the frontend)"),
        ],
        default="popular",
    )
    packages = blocks.ListBlock(PackageChooserBlock(), required=False, default=[])
    destination = DestinationChooserBlock(required=False)
    sdk_package_ids = blocks.ListBlock(
        blocks.CharBlock(max_length=120), required=False, default=[], label="SDK package ids"
    )
    limit = blocks.IntegerBlock(default=8, min_value=1, max_value=24)
    autoplay = blocks.BooleanBlock(required=False, default=False)
    show_price = blocks.BooleanBlock(required=False, default=True)
    cta = ButtonBlock(required=False)

    class Meta:
        icon = "list-ul"
        label = "Package carousel"
        group = "Sections"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        data["resolved_packages"] = _resolve_packages(value)
        return data


class PackageGridBlock(PopularPackagesBlock):
    """→ `PackageGrid.tsx` — same data as the carousel, laid out as a grid."""

    component = "PackageGrid"

    columns = blocks.ChoiceBlock(
        choices=[("2", "2 columns"), ("3", "3 columns"), ("4", "4 columns")], default="3"
    )

    class Meta:
        icon = "grip"
        label = "Package grid"
        group = "Sections"


class PackageListingBlock(SectionBlock):
    """→ `PopularPackagesGrid.tsx`, the filterable package catalogue."""

    component = "PackageListing"

    heading = blocks.CharBlock(default="Popular Packages", max_length=200)
    categories = blocks.ListBlock(blocks.CharBlock(max_length=60), required=False, default=[])
    page_size = blocks.IntegerBlock(default=6, min_value=1, max_value=48)
    default_category = blocks.CharBlock(required=False, max_length=60)
    show_filters = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "list-ul"
        label = "Package listing"
        group = "Sections"


def _resolve_packages(value):
    """Turn the block's source choice into a concrete list of package payloads."""
    from apps.catalog.models import Package

    source = value.get("source")
    limit = value.get("limit") or 8

    if source == "selected":
        return [serialize_package(package) for package in value.get("packages") or [] if package]
    if source == "destination" and value.get("destination"):
        queryset = Package.objects.filter(is_active=True, destination=value["destination"])
    elif source == "popular":
        queryset = Package.objects.filter(is_active=True, is_popular=True)
    else:  # sdk — the frontend resolves these ids against the Travories SDK
        return []
    return [serialize_package(package) for package in queryset[:limit]]


class ExperienceShowcaseBlock(SectionBlock):
    """→ `src/components/sections/ExperienceSection.tsx`"""

    component = "ExperienceSection"

    heading = blocks.CharBlock(max_length=250)
    description = blocks.TextBlock(required=False)
    description_highlight = blocks.CharBlock(required=False, max_length=250)
    show_arrows = blocks.BooleanBlock(required=False, default=True)
    small_cards = blocks.ListBlock(DestinationCardBlock(), required=False, default=[], max_num=6)
    feature_card = DestinationCardBlock(required=False, label="Large feature card")

    class Meta:
        icon = "duplicate"
        label = "Experience showcase"
        group = "Sections"


class WhyChooseUsCardBlock(blocks.StructBlock):
    theme = blocks.ChoiceBlock(choices=[("light", "Light"), ("dark", "Dark")], default="light")
    heading = blocks.CharBlock(max_length=120)
    heading_highlight = blocks.CharBlock(
        required=False, max_length=60, help_text="Word/phrase inside heading to accent (italic, green)."
    )
    description = blocks.TextBlock()
    description_highlight = blocks.CharBlock(
        required=False, max_length=200, help_text="Phrase inside description to accent."
    )
    image = APIImageChooserBlock(required=False, label="Circle image")
    link = LinkBlock(required=False)

    class Meta:
        icon = "pick"
        label = "Service card"


class WhyChooseUsBlock(SectionBlock):
    """→ `src/components/sections/WhyChooseUs.tsx`"""

    component = "WhyChooseUs"

    heading = HeadingGroupBlock()
    description_highlight = blocks.CharBlock(required=False, max_length=250)
    cards = blocks.ListBlock(WhyChooseUsCardBlock(), min_num=1, max_num=6)

    class Meta:
        icon = "pick"
        label = "Why choose us"
        group = "Sections"


class BentoGridBlock(SectionBlock):
    """
    → `WelcomeBentoGrid.tsx` and `SeasonalDestinationsBentoGrid.tsx`.

    Both are the same component with a different `variant` and item layout, so
    they share one block.
    """

    component = "BentoGrid"

    heading = HeadingGroupBlock()
    variant = blocks.ChoiceBlock(
        choices=[
            ("welcome", "Welcome — first tile is a large feature card"),
            ("seasonal", "Seasonal — uniform tiles with per-item layout"),
        ],
        default="welcome",
    )
    source = blocks.ChoiceBlock(
        choices=[
            ("selected", "Hand-picked cards"),
            ("featured", "Automatic — featured destinations"),
        ],
        default="selected",
    )
    items = blocks.ListBlock(DestinationCardBlock(), required=False, default=[], max_num=12)
    limit = blocks.IntegerBlock(default=6, min_value=1, max_value=12)

    class Meta:
        icon = "grip"
        label = "Bento grid"
        group = "Sections"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        if value.get("source") == "featured":
            from apps.catalog.models import Destination

            queryset = Destination.objects.filter(is_featured=True)[: value.get("limit") or 6]
            data["resolved_items"] = [
                {
                    **serialize_destination(destination),
                    "variant": "default",
                    "layout": destination.default_layout,
                    "href": destination.href or f"/destinations/{destination.slug}",
                }
                for destination in queryset
            ]
        else:
            data["resolved_items"] = data.get("items") or []
        return data


class DestinationsGridBlock(SectionBlock):
    """→ `DestinationsGrid.tsx`, a carousel backed by page-owned selections."""

    component = "DestinationsGrid"

    heading = blocks.CharBlock(default="Our Destinations", max_length=200)
    source = blocks.ChoiceBlock(
        choices=[("featured", "Automatic — featured destinations"), ("selected", "Hand-picked")],
        default="featured",
    )
    destinations = blocks.ListBlock(DestinationChooserBlock(), required=False, default=[])
    limit = blocks.IntegerBlock(default=12, min_value=1, max_value=48)

    class Meta:
        icon = "grip"
        label = "Destinations carousel"
        group = "Sections"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        if value.get("source") == "selected":
            data["resolved_items"] = data.get("destinations") or []
        else:
            from apps.catalog.models import Destination

            data["resolved_items"] = [
                serialize_destination(item)
                for item in Destination.objects.filter(is_featured=True)[: value.get("limit") or 12]
            ]
        return data


class DestinationDetailBlock(SectionBlock):
    """→ `DestinationDetail.tsx`; data is chosen by this page block."""

    component = "DestinationDetail"
    destination = DestinationDetailChooserBlock()

    class Meta:
        icon = "site"
        label = "Destination detail"
        group = "Page templates"


class PackageDetailBlock(SectionBlock):
    """→ `PackageDetail.tsx`; data is chosen by this page block."""

    component = "PackageDetail"
    package = PackageDetailChooserBlock()
    reserve_href = blocks.CharBlock(required=False, max_length=255)

    class Meta:
        icon = "doc-full"
        label = "Package detail"
        group = "Page templates"


class FeatureItemBlock(blocks.StructBlock):
    number = blocks.CharBlock(required=False, max_length=8, help_text="e.g. 01 — auto-numbered if blank.")
    title = blocks.CharBlock(max_length=160)
    description = blocks.TextBlock(required=False)
    icon = IconBlock()

    class Meta:
        icon = "list-ol"
        label = "Feature"


class FeaturesListBlock(SectionBlock):
    """→ `src/components/sections/FeaturesList.tsx`"""

    component = "FeaturesList"

    heading = blocks.CharBlock(max_length=250)
    description = blocks.TextBlock(required=False)
    description_highlight = blocks.CharBlock(required=False, max_length=250)
    image = APIImageChooserBlock(required=False, label="Decorative image")
    image_position = blocks.ChoiceBlock(
        choices=[("left", "Left"), ("right", "Right")], default="left"
    )
    items = blocks.ListBlock(FeatureItemBlock(), min_num=1, max_num=8)

    class Meta:
        icon = "list-ol"
        label = "Features list"
        group = "Sections"


class TestimonialBlock(SectionBlock):
    """→ `src/components/sections/Testimonial.tsx` (single quote over a photo)"""

    component = "Testimonial"

    background_image = APIImageChooserBlock(required=False)
    background_video = VideoChooserBlock(required=False)
    overlay_opacity = blocks.IntegerBlock(default=70, min_value=0, max_value=100)
    testimonial = TestimonialChooserBlock(
        required=False, help_text="Pick from the testimonial library, or fill in the fields below."
    )
    quote = blocks.TextBlock(required=False)
    quote_highlights = blocks.ListBlock(
        blocks.CharBlock(max_length=120),
        required=False,
        default=[],
        help_text="Phrases inside the quote to accent in brand green.",
    )
    author_name = blocks.CharBlock(required=False, max_length=120)
    author_role = blocks.CharBlock(required=False, max_length=160)
    show_quote_icon = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "openquote"
        label = "Testimonial (feature)"
        group = "Sections"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        chosen = data.get("testimonial") or {}
        data["quote"] = data.get("quote") or chosen.get("quote") or ""
        data["author_name"] = data.get("author_name") or chosen.get("author_name") or ""
        data["author_role"] = data.get("author_role") or chosen.get("author_role") or ""
        return data


class TestimonialsCarouselBlock(SectionBlock):
    """→ `TestimonialsCarousel.tsx` — several reviews side by side."""

    component = "TestimonialsCarousel"

    heading = HeadingGroupBlock()
    source = blocks.ChoiceBlock(
        choices=[("featured", "Automatic — featured testimonials"), ("selected", "Hand-picked")],
        default="featured",
    )
    testimonials = blocks.ListBlock(TestimonialChooserBlock(), required=False, default=[])
    limit = blocks.IntegerBlock(default=6, min_value=1, max_value=24)
    autoplay = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "openquote"
        label = "Testimonials carousel"
        group = "Sections"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        if value.get("source") == "featured":
            from apps.catalog.models import Testimonial

            queryset = Testimonial.objects.filter(is_featured=True)[: value.get("limit") or 6]
            data["resolved_testimonials"] = [serialize_testimonial(item) for item in queryset]
        else:
            data["resolved_testimonials"] = data.get("testimonials") or []
        return data


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(max_length=250)
    answer = APIRichTextBlock(required=False)
    open_by_default = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "help"
        label = "Question"


class FAQBlock(SectionBlock):
    """→ `src/components/sections/FAQSection.tsx`"""

    component = "FAQSection"

    heading = HeadingGroupBlock()
    items = blocks.ListBlock(FAQItemBlock(), min_num=1)
    show_side_card = blocks.BooleanBlock(required=False, default=True)
    side_card_heading = blocks.CharBlock(required=False, max_length=160)
    side_card_text = blocks.TextBlock(required=False)
    side_card_button = ButtonBlock(required=False)

    class Meta:
        icon = "help"
        label = "FAQ"
        group = "Sections"


class StatsBannerBlock(SectionBlock):
    """→ `src/components/sections/StatsSection.tsx` (stats over a photo)"""

    component = "StatsSection"

    background_image = APIImageChooserBlock(required=False)
    background_video = VideoChooserBlock(required=False)
    overlay_opacity = blocks.IntegerBlock(default=75, min_value=0, max_value=100)
    heading = blocks.CharBlock(required=False, max_length=200)
    stats = blocks.ListBlock(StatBlock(), min_num=1, max_num=6)

    class Meta:
        icon = "form"
        label = "Stats banner"
        group = "Sections"


class CTABannerBlock(SectionBlock):
    """→ `CTABanner.tsx`"""

    component = "CTABanner"

    heading = blocks.CharBlock(max_length=200)
    heading_highlight = blocks.CharBlock(
        required=False, max_length=60, help_text="Word/phrase inside heading to accent (italic, green)."
    )
    text = blocks.TextBlock(required=False)
    background_image = APIImageChooserBlock(required=False)
    buttons = blocks.ListBlock(ButtonBlock(), required=False, default=[], max_num=3)

    class Meta:
        icon = "bullhorn"
        label = "CTA banner"
        group = "Sections"


class CulturalToursBlock(PopularPackagesBlock):
    """→ `CulturalDayTours.tsx`, with content owned by the containing page."""

    component = "CulturalDayTours"

    heading = blocks.CharBlock(default="Cultural & Day Tours", max_length=200)
    description = blocks.TextBlock(required=False)

    class Meta:
        icon = "list-ul"
        label = "Cultural & day tours"
        group = "Sections"


class RichTextSectionBlock(SectionBlock):
    """→ `RichTextSection.tsx` — freeform editorial content."""

    component = "RichTextSection"

    heading = blocks.CharBlock(required=False, max_length=200)
    body = APIRichTextBlock()
    width = blocks.ChoiceBlock(
        choices=[("narrow", "Narrow (prose)"), ("default", "Default")], default="narrow"
    )

    class Meta:
        icon = "doc-full"
        label = "Rich text"
        group = "Sections"


class GalleryItemBlock(blocks.StructBlock):
    image = APIImageChooserBlock()
    caption = blocks.CharBlock(required=False, max_length=200)
    link = LinkBlock(required=False)

    class Meta:
        icon = "image"
        label = "Gallery image"


class GalleryBlock(SectionBlock):
    """→ `Gallery.tsx`"""

    component = "Gallery"

    heading = HeadingGroupBlock()
    layout = blocks.ChoiceBlock(
        choices=[("grid", "Grid"), ("masonry", "Masonry"), ("carousel", "Carousel")], default="grid"
    )
    columns = blocks.ChoiceBlock(
        choices=[("2", "2"), ("3", "3"), ("4", "4")], default="3"
    )
    images = blocks.ListBlock(GalleryItemBlock(), min_num=1)
    enable_lightbox = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "image"
        label = "Gallery"
        group = "Sections"


class VideoSectionBlock(SectionBlock):
    """→ `VideoSection.tsx` — a self-hosted or embedded video."""

    component = "VideoSection"

    heading = HeadingGroupBlock()
    media = MediaBlock()
    aspect_ratio = blocks.ChoiceBlock(
        choices=[("16/9", "16:9"), ("4/3", "4:3"), ("1/1", "Square"), ("21/9", "Ultrawide")],
        default="16/9",
    )
    rounded = blocks.BooleanBlock(required=False, default=True)

    class Meta:
        icon = "media"
        label = "Video"
        group = "Sections"


class FormFieldBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=60, help_text="Field key sent to the API, e.g. full_name.")
    label = blocks.CharBlock(max_length=120)
    field_type = blocks.ChoiceBlock(
        choices=[
            ("text", "Text"),
            ("email", "Email"),
            ("tel", "Phone"),
            ("number", "Number"),
            ("date", "Date"),
            ("textarea", "Long text"),
            ("select", "Dropdown"),
            ("checkbox", "Checkbox"),
        ],
        default="text",
    )
    placeholder = blocks.CharBlock(required=False, max_length=120)
    required = blocks.BooleanBlock(required=False, default=False)
    options = blocks.ListBlock(
        blocks.CharBlock(max_length=120),
        required=False,
        default=[],
        help_text="Dropdown options (dropdown fields only).",
    )
    width = blocks.ChoiceBlock(choices=[("full", "Full"), ("half", "Half")], default="full")

    class Meta:
        icon = "form"
        label = "Form field"


class LeadFormBlock(SectionBlock):
    """→ `LeadForm.tsx` — posts to /api/v2/leads/."""

    component = "LeadForm"

    heading = HeadingGroupBlock()
    form_key = blocks.CharBlock(
        max_length=60,
        default="enquiry",
        help_text="Groups submissions in the admin, e.g. enquiry, newsletter.",
    )
    fields = blocks.ListBlock(FormFieldBlock(), min_num=1)
    submit_label = blocks.CharBlock(default="Send enquiry", max_length=60)
    success_message = blocks.TextBlock(default="Thanks! We'll get back to you shortly.")
    notification_email = blocks.EmailBlock(
        required=False, help_text="Where submissions are emailed. Defaults to the site setting."
    )

    class Meta:
        icon = "mail"
        label = "Lead form"
        group = "Sections"


class PackageEnquiryBlock(SectionBlock):
    component = "PackageEnquiry"
    package = PackageDetailChooserBlock(required=False, help_text="Optional default package for this page.")

    class Meta:
        icon = "mail"
        label = "Package enquiry"
        group = "Page templates"


class CheckoutBlock(SectionBlock):
    component = "Checkout"

    class Meta:
        icon = "credit-card"
        label = "Checkout"
        group = "Page templates"


class PaymentSuccessBlock(SectionBlock):
    component = "PaymentSuccess"

    class Meta:
        icon = "tick"
        label = "Payment success"
        group = "Page templates"


class SpacerBlock(SectionBlock):
    """→ `Spacer.tsx` — vertical breathing room / divider."""

    component = "Spacer"

    size = blocks.ChoiceBlock(
        choices=[("sm", "Small"), ("md", "Medium"), ("lg", "Large"), ("xl", "Extra large")],
        default="md",
    )
    show_divider = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "horizontalrule"
        label = "Spacer / divider"
        group = "Layout"


class AuthenticExperienceItemBlock(blocks.StructBlock):
    number = blocks.CharBlock(
        required=False, max_length=8, help_text="e.g. 01 — auto-numbered if blank."
    )
    title = blocks.CharBlock(max_length=160)
    description = blocks.TextBlock(required=False)

    class Meta:
        icon = "list-ol"
        label = "Experience item"


class AuthenticExperiencesBlock(SectionBlock):
    """→ `src/components/sections/AuthenticExperiences.tsx`"""

    component = "AuthenticExperiences"

    heading = blocks.CharBlock(
        max_length=250, default="Discover Nepal Through Authentic Experiences with Us"
    )
    description = blocks.TextBlock(required=False)
    description_highlight = blocks.CharBlock(
        required=False,
        max_length=250,
        help_text="Trailing phrase inside the description to render in muted italic.",
    )
    image = APIImageChooserBlock(required=False)
    items = blocks.ListBlock(AuthenticExperienceItemBlock(), min_num=1, max_num=6)
    reversed = blocks.BooleanBlock(
        required=False, default=False, help_text="Image on the right instead of the left."
    )

    class Meta:
        icon = "duplicate"
        label = "Authentic experiences"
        group = "Sections"


class EmbedSectionBlock(SectionBlock):
    """→ `EmbedSection.tsx` — maps, third-party widgets, social embeds."""

    component = "EmbedSection"

    heading = HeadingGroupBlock()
    embed = APIEmbedBlock(required=False)
    raw_html = blocks.RawHTMLBlock(
        required=False, help_text="Only for trusted widgets — rendered as-is by the frontend."
    )

    class Meta:
        icon = "code"
        label = "Embed"
        group = "Sections"
