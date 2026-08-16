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

SECTION_BLOCKS = [
    # name in the API              block class
    ("hero", sections.HeroBlock()),
    ("header_card", sections.HeaderCardBlock()),
    ("page_hero", sections.PageHeroBlock()),
    ("contact_hero", sections.ContactHeroBlock()),
    ("contact_form", sections.ContactFormBlock()),
    ("intro_stats", sections.IntroStatsBlock()),
    ("popular_packages", sections.PopularPackagesBlock()),
    ("package_grid", sections.PackageGridBlock()),
    ("package_listing", sections.PackageListingBlock()),
    ("experience_showcase", sections.ExperienceShowcaseBlock()),
    ("why_choose_us", sections.WhyChooseUsBlock()),
    ("authentic_experiences", sections.AuthenticExperiencesBlock()),
    ("bento_grid", sections.BentoGridBlock()),
    ("destinations_grid", sections.DestinationsGridBlock()),
    ("destination_detail", sections.DestinationDetailBlock()),
    ("package_detail", sections.PackageDetailBlock()),
    ("features_list", sections.FeaturesListBlock()),
    ("testimonial", sections.TestimonialBlock()),
    ("testimonials_carousel", sections.TestimonialsCarouselBlock()),
    ("faq", sections.FAQBlock()),
    ("stats_banner", sections.StatsBannerBlock()),
    ("cta_banner", sections.CTABannerBlock()),
    ("cultural_tours", sections.CulturalToursBlock()),
    ("rich_text", sections.RichTextSectionBlock()),
    ("gallery", sections.GalleryBlock()),
    ("video", sections.VideoSectionBlock()),
    ("embed", sections.EmbedSectionBlock()),
    ("lead_form", sections.LeadFormBlock()),
    ("package_enquiry", sections.PackageEnquiryBlock()),
    ("checkout", sections.CheckoutBlock()),
    ("payment_success", sections.PaymentSuccessBlock()),
    ("spacer", sections.SpacerBlock()),
]

BLOCK_TYPES = [name for name, _ in SECTION_BLOCKS]

#: `{block type -> React component name}` — served at /api/v2/block-registry/
#: so the frontend can assert both sides are in sync.
COMPONENT_MAP = {
    name: getattr(block, "component", "") or name for name, block in SECTION_BLOCKS
}
