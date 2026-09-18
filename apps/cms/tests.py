import json

from django.test import SimpleTestCase

from apps.cms.blocks import SECTION_BLOCKS
from apps.cms.models import (
    BlogIndexPage,
    BlogPostPage,
    CheckoutPage,
    ContactPage,
    DestinationDetailPage,
    DestinationIndexPage,
    EnquiryPage,
    HomePage,
    PackageDetailPage,
    PackageIndexPage,
    PaymentSuccessPage,
    PrivacyPage,
    StandardPage,
)
from apps.cms.management.commands.organize_blog_post_pages import organize_body


PAGE_TYPES_WITH_SECTIONS = (
    HomePage,
    StandardPage,
    ContactPage,
    PrivacyPage,
    DestinationIndexPage,
    DestinationDetailPage,
    PackageIndexPage,
    PackageDetailPage,
    BlogIndexPage,
    BlogPostPage,
    EnquiryPage,
    CheckoutPage,
    PaymentSuccessPage,
)

EXPECTED_PAGE_BLOCKS = {
    HomePage: {"hero", "intro_stats", "popular_packages", "experience_showcase", "why_choose_us", "bento_grid", "authentic_experiences", "faq", "cta_banner"},
    StandardPage: {"page_hero", "header_card", "destinations_grid", "lead_form", "rich_text", "gallery", "video", "embed", "faq", "cta_banner", "spacer"},
    ContactPage: {"contact_hero", "contact_form", "why_choose_us", "authentic_experiences", "faq"},
    PrivacyPage: {"page_hero", "rich_text", "faq", "cta_banner"},
    DestinationIndexPage: {"page_hero", "destinations_grid", "experience_showcase", "cta_banner"},
    DestinationDetailPage: {"destination_header", "destination_overview", "destination_packages", "cta_banner"},
    PackageIndexPage: {"page_hero", "package_listing", "cultural_tours", "cta_banner"},
    PackageDetailPage: {"package_header", "package_overview", "package_booking", "package_itinerary", "package_reviews", "cta_banner"},
    BlogIndexPage: {"page_hero", "blog_listing", "cta_banner"},
    BlogPostPage: {"blog_article_header", "blog_article_body", "blog_related_stories", "cta_banner"},
    EnquiryPage: {"page_hero", "package_enquiry", "cta_banner"},
    CheckoutPage: {"checkout"},
    PaymentSuccessPage: {"payment_success", "cta_banner"},
}

EXPECTED_EDITOR_TABS = {
    HomePage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    StandardPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    ContactPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    PrivacyPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    DestinationIndexPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    DestinationDetailPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    PackageIndexPage: ["Content", "Listing options", "Page layout", "SEO & sharing", "Settings"],
    PackageDetailPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    BlogIndexPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    BlogPostPage: ["Story", "Publishing details", "Page layout", "SEO & sharing", "Settings"],
    EnquiryPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    CheckoutPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
    PaymentSuccessPage: ["Content", "Page layout", "SEO & sharing", "Settings"],
}


class PageSectionEditorTests(SimpleTestCase):
    def setUp(self):
        self.stream_block = HomePage._meta.get_field("body").stream_block

    def test_sections_are_collapsed_by_default(self):
        for page_type in PAGE_TYPES_WITH_SECTIONS:
            with self.subTest(page_type=page_type.__name__):
                stream_block = page_type._meta.get_field("body").stream_block
                self.assertTrue(stream_block.meta.collapsed)

    def test_each_page_type_only_offers_relevant_sections(self):
        for page_type, expected_blocks in EXPECTED_PAGE_BLOCKS.items():
            with self.subTest(page_type=page_type.__name__):
                stream_block = page_type._meta.get_field("body").stream_block
                self.assertEqual(set(stream_block.child_blocks), expected_blocks)

    def test_section_picker_uses_clear_categories(self):
        groups = {block.meta.group for _, block in SECTION_BLOCKS}

        self.assertEqual(
            groups,
            {
                "Actions & forms",
                "Content & media",
                "Destinations & experiences",
                "Layout",
                "Packages",
                "Page headers",
                "Page templates",
                "Trust & information",
            },
        )
        self.assertNotIn("Sections", groups)

    def test_editor_separates_content_from_page_layout(self):
        for page_type, expected_tabs in EXPECTED_EDITOR_TABS.items():
            with self.subTest(page_type=page_type.__name__):
                tabs = [tab.heading for tab in page_type.get_edit_handler().children]
                self.assertEqual(tabs, expected_tabs)


class BlogPostOrganizationTests(SimpleTestCase):
    def test_adds_article_screens_before_existing_cta(self):
        body = json.dumps([
            {"type": "cta_banner", "value": {"heading": "Book now"}, "id": "cta"}
        ])

        organized, changed = organize_body(body)

        self.assertTrue(changed)
        self.assertEqual(
            [block["type"] for block in json.loads(organized)],
            [
                "blog_article_header",
                "blog_article_body",
                "blog_related_stories",
                "cta_banner",
            ],
        )

    def test_is_idempotent(self):
        organized, _ = organize_body([])

        second, changed = organize_body(organized)

        self.assertFalse(changed)
        self.assertEqual(second, organized)
