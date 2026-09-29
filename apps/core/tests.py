"""Lumora Admin: sidebar structure, editorial cross-links and headless page URLs."""

import json
import re

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from wagtail.models import Page, Site

from apps.catalog.models import Destination, Package
from apps.cms.models import BlogIndexPage, BlogPostPage, HomePage, PackageIndexPage
from apps.core.blocks import LinkBlock

FRONTEND = "https://www.example.com"


@override_settings(FRONTEND_BASE_URL=FRONTEND)
class LumoraAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        root = Page.get_first_root_node()
        cls.home = HomePage(title="Home", slug="lumora-home")
        root.add_child(instance=cls.home)
        Site.objects.update(root_page=cls.home, is_default_site=True)
        cls.home.add_child(instance=PackageIndexPage(title="Packages", slug="packages"))
        cls.blog_index = BlogIndexPage(title="Blog", slug="blog")
        cls.home.add_child(instance=cls.blog_index)
        cls.post = BlogPostPage(title="Trek notes", slug="trek-notes", category="Guides")
        cls.blog_index.add_child(instance=cls.post)
        cls.destination = Destination.objects.create(title="Annapurna", region="Annapurna")
        cls.admin = get_user_model().objects.create_superuser("editor", "editor@example.com", "unused")

    def setUp(self):
        self.client.force_login(self.admin)

    def create_package(self):
        with self.captureOnCommitCallbacks(execute=True):
            return Package.objects.create(title="Annapurna Base Camp", price=650, destination=self.destination)

    # -- Headless page URLs --------------------------------------------------

    def test_page_urls_point_at_the_frontend(self):
        self.assertEqual(self.post.url, f"{FRONTEND}/blog/trek-notes")
        self.assertEqual(self.post.seo["canonical_url"], f"{FRONTEND}/blog/trek-notes")
        self.assertEqual(self.home.url, f"{FRONTEND}/")

    def test_package_page_url_matches_package_public_url(self):
        package = self.create_package()
        self.assertEqual(package.detail_page.url, f"{FRONTEND}{package.public_url}")

    def test_legacy_cms_preview_links_redirect_to_the_frontend(self):
        response = self.client.get("/cms-preview/blog/trek-notes/")
        self.assertRedirects(response, f"{FRONTEND}/blog/trek-notes", fetch_redirect_response=False)

    def test_page_links_in_blocks_resolve_to_frontend_paths(self):
        link = LinkBlock().to_python({"link_type": "page", "page": self.post.pk})
        self.assertEqual(LinkBlock().get_api_representation(link)["href"], "/blog/trek-notes")

    def test_template_preview_is_disabled_for_headless_pages(self):
        self.assertFalse(self.post.is_previewable())

    # -- Admin shell ---------------------------------------------------------

    def sidebar_labels(self):
        html = self.client.get("/admin/").content.decode()
        props = json.loads(re.search(r'id="wagtail-sidebar-props"[^>]*>(.*?)</script>', html, re.S).group(1))
        menu = next(m for m in props["modules"] if m["_type"].endswith("MainMenuModule"))
        return [item["_args"][0]["label"] for item in menu["_args"][0]]

    def test_sidebar_puts_editorial_sections_first(self):
        self.assertEqual(
            self.sidebar_labels(),
            [
                "Pages",
                "Blog",
                "Packages",
                "Destinations",
                "Testimonials",
                "Leads",
                "Media",
                "Site settings",
                "Reports",
                "Administration",
                "Help",
            ],
        )

    def test_admin_is_branded_lumora(self):
        html = self.client.get("/admin/").content.decode()
        self.assertIn("<title>Dashboard - Lumora Admin</title>", html)
        self.assertIn("lumora_admin/admin.css", html)
        self.client.logout()
        self.assertContains(self.client.get("/admin/login/"), "Sign in to Lumora Admin")

    def test_blog_listing_shows_posts(self):
        response = self.client.get("/admin/blog/")
        self.assertContains(response, "Trek notes")

    def test_dashboard_offers_quick_actions(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "Write a blog post")
        self.assertContains(response, "Add a package")

    # -- Editorial cross-links -----------------------------------------------

    def test_package_edit_links_to_its_page_destination_and_leads(self):
        package = self.create_package()
        response = self.client.get(f"/admin/snippets/catalog/package/edit/{package.pk}/")
        self.assertContains(response, f"/admin/pages/{package.detail_page.pk}/edit/")
        self.assertContains(response, f"/admin/snippets/catalog/destination/edit/{self.destination.pk}/")
        self.assertContains(response, f"/admin/snippets/leads/leadsubmission/?package={package.pk}")
        self.assertContains(response, "What&#x27;s included / excluded")

    def test_package_page_links_back_to_package_data(self):
        package = self.create_package()
        response = self.client.get(f"/admin/pages/{package.detail_page.pk}/edit/")
        self.assertContains(response, f"/admin/snippets/catalog/package/edit/{package.pk}/")

    def test_destination_edit_links_to_its_packages(self):
        response = self.client.get(f"/admin/snippets/catalog/destination/edit/{self.destination.pk}/")
        self.assertContains(response, f"/admin/snippets/catalog/package/?destination={self.destination.pk}")

    def test_package_listing_filters_by_destination_and_searches_destination_name(self):
        package = self.create_package()
        Package.objects.create(title="Chitwan Safari", price=300)
        by_filter = self.client.get(f"/admin/snippets/catalog/package/?destination={self.destination.pk}")
        by_search = self.client.get("/admin/snippets/catalog/package/?q=annapurna")
        for response in (by_filter, by_search):
            self.assertContains(response, package.title)
            self.assertNotContains(response, "Chitwan Safari")
