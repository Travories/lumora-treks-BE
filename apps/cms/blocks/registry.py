"""
The block registry — the single place where a frontend component becomes
available to editors.

To register a new frontend component:

1. Write the block in `sections.py`, set `component = "<ReactComponentName>"`.
2. Add one line to `SECTION_BLOCKS` below.
3. `python manage.py makemigrations cms && python manage.py migrate`.
4. Frontend: add `'<ReactComponentName>': Component` to its block registry.

`BLOCK_TYPES` (the StreamField block name, e.g. `hero`) is what appears as
`type` in the API; `component` is what the frontend keys off.
"""

from apps.cms.blocks import sections


# Store block classes rather than shared instances. Each StreamField receives
# fresh block objects, avoiding Wagtail binding the same block state to several
# page models when we build page-specific section libraries.
SECTION_BLOCK_FACTORIES = [
    # name in the API              block class
    ("hero", sections.HeroBlock),
    ("header_card", sections.HeaderCardBlock),
    ("page_hero", sections.PageHeroBlock),
    ("contact_hero", sections.ContactHeroBlock),
    ("contact_form", sections.ContactFormBlock),
    ("intro_stats", sections.IntroStatsBlock),
    ("popular_packages", sections.PopularPackagesBlock),
    ("package_grid", sections.PackageGridBlock),
    ("package_listing", sections.PackageListingBlock),
    ("blog_listing", sections.BlogListingBlock),
    ("blog_article_header", sections.BlogArticleHeaderBlock),
    ("blog_article_body", sections.BlogArticleBodyBlock),
    ("blog_related_stories", sections.BlogRelatedStoriesBlock),
    ("experience_showcase", sections.ExperienceShowcaseBlock),
    ("why_choose_us", sections.WhyChooseUsBlock),
    ("authentic_experiences", sections.AuthenticExperiencesBlock),
    ("bento_grid", sections.BentoGridBlock),
    ("destinations_grid", sections.DestinationsGridBlock),
    ("destination_detail", sections.DestinationDetailBlock),
    ("destination_header", sections.DestinationHeaderBlock),
    ("destination_overview", sections.DestinationOverviewBlock),
    ("destination_packages", sections.DestinationPackagesBlock),
    ("package_detail", sections.PackageDetailBlock),
    ("package_header", sections.PackageHeaderBlock),
    ("package_overview", sections.PackageOverviewBlock),
    ("package_booking", sections.PackageBookingBlock),
    ("package_itinerary", sections.PackageItineraryBlock),
    ("package_reviews", sections.PackageReviewsBlock),
    ("features_list", sections.FeaturesListBlock),
    ("testimonial", sections.TestimonialBlock),
    ("testimonials_carousel", sections.TestimonialsCarouselBlock),
    ("faq", sections.FAQBlock),
    ("stats_banner", sections.StatsBannerBlock),
    ("cta_banner", sections.CTABannerBlock),
    ("cultural_tours", sections.CulturalToursBlock),
    ("rich_text", sections.RichTextSectionBlock),
    ("gallery", sections.GalleryBlock),
    ("video", sections.VideoSectionBlock),
    ("embed", sections.EmbedSectionBlock),
    ("lead_form", sections.LeadFormBlock),
    ("package_enquiry", sections.PackageEnquiryBlock),
    ("checkout", sections.CheckoutBlock),
    ("payment_success", sections.PaymentSuccessBlock),
    ("spacer", sections.SpacerBlock),
]


def section_blocks(*names):
    """Return fresh block instances for a page-specific StreamField."""

    requested = set(names)
    available = {name for name, _ in SECTION_BLOCK_FACTORIES}
    unknown = requested - available
    if unknown:
        raise ValueError(f"Unknown CMS section block(s): {', '.join(sorted(unknown))}")
    return [(name, block_class()) for name, block_class in SECTION_BLOCK_FACTORIES if name in requested]


SECTION_BLOCKS = section_blocks(*(name for name, _ in SECTION_BLOCK_FACTORIES))

BLOCK_TYPES = [name for name, _ in SECTION_BLOCKS]

#: `{block type -> React component name}` — served at /api/v2/block-registry/
#: so the frontend can assert both sides are in sync.
COMPONENT_MAP = {
    name: getattr(block, "component", "") or name for name, block in SECTION_BLOCKS
}
