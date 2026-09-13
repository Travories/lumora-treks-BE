import io
import json

from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Page

from apps.catalog.models import Destination, Package
from apps.cms.models import (
    CheckoutPage,
    ContactPage,
    DestinationDetailPage,
    DestinationIndexPage,
    EnquiryPage,
    HomePage,
    PackageDetailPage,
    PackageFolderPage,
    PackageIndexPage,
    PaymentSuccessPage,
    PrivacyPage,
    StandardPage,
)


class ConvertLegacyDetailPagesTests(TestCase):
    def setUp(self):
        # Create catalog records before their indexes, so the package signal
        # cannot eagerly create the dedicated pages this command is testing.
        self.destination = Destination.objects.create(title="Nepal", slug="nepal")
        self.package = Package.objects.create(title="Everest Base Camp", price=1200)

        root = Page.get_first_root_node()
        self.home = HomePage(title="Conversion home", slug="conversion-home")
        root.add_child(instance=self.home)

        self.destination_index = StandardPage(
            title="Destinations", slug="destinations", intro="Keep this introduction"
        )
        self.home.add_child(instance=self.destination_index)
        self.destination_detail = StandardPage(
            title="Nepal", slug=self.destination.slug, intro="Obsolete detail introduction"
        )
        self.destination_index.add_child(instance=self.destination_detail)

        self.package_index = PackageIndexPage(title="Packages", slug="packages")
        self.home.add_child(instance=self.package_index)
        self.package_folder = StandardPage(title=self.package.title, slug=self.package.slug)
        self.package_index.add_child(instance=self.package_folder)
        self.package_detail = StandardPage(
            title=self.package.title,
            slug=self.package.public_code,
            intro="Obsolete package introduction",
        )
        self.package_folder.add_child(instance=self.package_detail)

        StandardPage.objects.filter(pk=self.destination_detail.pk).update(
            body=json.dumps(
                [
                    {
                        "type": "destination_detail",
                        "value": {"destination": self.destination.pk, "settings": {}},
                        "id": "legacy-destination-detail",
                    }
                ]
            )
        )
        self.destination_detail.refresh_from_db()
        StandardPage.objects.filter(pk=self.package_detail.pk).update(
            body=json.dumps(
                [
                    {
                        "type": "package_detail",
                        "value": {
                            "package": self.package.pk,
                            "reserve_href": "/custom-enquiry",
                            "settings": {},
                        },
                        "id": "legacy-package-detail",
                    }
                ]
            )
        )
        self.package_detail.refresh_from_db()

        self.destination_index_revision = self.destination_index.save_revision()
        self.destination_detail_revision = self.destination_detail.save_revision()
        revision_content = dict(self.destination_detail_revision.content)
        revision_content["body"] = json.dumps(
            [
                {
                    "type": "destination_detail",
                    "value": {"destination": self.destination.pk, "settings": {}},
                    "id": "legacy-destination-detail-revision",
                }
            ]
        )
        self.destination_detail_revision.content = revision_content
        self.destination_detail_revision.save(update_fields=["content"])
        self.package_folder_revision = self.package_folder.save_revision()
        self.package_detail_revision = self.package_detail.save_revision()
        revision_content = dict(self.package_detail_revision.content)
        revision_content["body"] = json.dumps(
            [
                {
                    "type": "package_detail",
                    "value": {
                        "package": self.package.pk,
                        "reserve_href": "/custom-enquiry",
                        "settings": {},
                    },
                    "id": "legacy-package-detail-revision",
                }
            ]
        )
        self.package_detail_revision.content = revision_content
        self.package_detail_revision.save(update_fields=["content"])

    def test_apply_converts_complete_pairs_and_rewrites_revisions(self):
        call_command("convert_legacy_detail_pages", "--apply")

        converted_index = DestinationIndexPage.objects.get(pk=self.destination_index.pk)
        self.assertEqual(converted_index.intro, "Keep this introduction")
        self.assertEqual(
            DestinationDetailPage.objects.get(pk=self.destination_detail.pk).destination,
            self.destination,
        )
        self.assertTrue(PackageFolderPage.objects.filter(pk=self.package_folder.pk).exists())
        self.assertEqual(
            PackageDetailPage.objects.get(pk=self.package_detail.pk).package,
            self.package,
        )

        self.destination_index_revision.refresh_from_db()
        self.assertEqual(
            self.destination_index_revision.content_type,
            DestinationIndexPage.objects.get(pk=self.destination_index.pk).content_type,
        )
        self.assertEqual(
            self.destination_index_revision.content["content_type"],
            self.destination_index_revision.content_type_id,
        )
        self.assertEqual(self.destination_index_revision.content["intro"], "Keep this introduction")

        self.destination_detail_revision.refresh_from_db()
        self.assertEqual(
            self.destination_detail_revision.content["destination"], self.destination.pk
        )
        self.assertNotIn("intro", self.destination_detail_revision.content)
        self.assertEqual(
            self.destination_detail_revision.content["content_type"],
            self.destination_detail_revision.content_type_id,
        )

        self.package_detail_revision.refresh_from_db()
        self.assertEqual(self.package_detail_revision.content["package"], self.package.pk)
        self.assertNotIn("intro", self.package_detail_revision.content)
        self.assertEqual(
            self.package_detail_revision.content["content_type"],
            self.package_detail_revision.content_type_id,
        )

        self.package_folder_revision.refresh_from_db()
        self.assertEqual(self.package_folder_revision.content_type.model, "packagefolderpage")
        self.assertEqual(
            self.package_folder_revision.content["content_type"],
            self.package_folder_revision.content_type_id,
        )

        # The rewritten payloads are not merely internally consistent: Wagtail
        # can materialise the new concrete page types from them.
        self.assertIsInstance(self.destination_detail_revision.as_object(), DestinationDetailPage)

        call_command("split_package_detail_pages", "--apply")
        converted_package = PackageDetailPage.objects.get(pk=self.package_detail.pk)
        self.assertEqual(
            [block["type"] for block in converted_package.body.raw_data],
            ["package_header", "package_overview", "package_booking", "package_itinerary", "package_reviews"],
        )
        self.assertEqual(converted_package.body.raw_data[2]["value"]["reserve_href"], "/custom-enquiry")
        self.package_detail_revision.refresh_from_db()
        self.assertNotIn("package_detail", self.package_detail_revision.content["body"])
        self.assertIsInstance(self.package_detail_revision.as_object(), PackageDetailPage)

        call_command("split_destination_detail_pages", "--apply")
        converted_detail = DestinationDetailPage.objects.get(pk=self.destination_detail.pk)
        self.assertEqual(
            [block["type"] for block in converted_detail.body.raw_data],
            ["destination_header", "destination_overview", "destination_packages"],
        )
        self.destination_detail_revision.refresh_from_db()
        self.assertEqual(
            [block["type"] for block in json.loads(self.destination_detail_revision.content["body"])],
            ["destination_header", "destination_overview", "destination_packages"],
        )
        self.assertIsInstance(self.destination_detail_revision.as_object(), DestinationDetailPage)

    def test_incomplete_package_pair_is_not_converted(self):
        incomplete_package = Package.objects.create(title="Incomplete trek", price=500)
        incomplete_folder = StandardPage(
            title=incomplete_package.title, slug=incomplete_package.slug
        )
        self.package_index.add_child(instance=incomplete_folder)

        call_command("convert_legacy_detail_pages", "--apply")

        incomplete_folder.refresh_from_db()
        self.assertEqual(incomplete_folder.content_type.model, "standardpage")
        self.assertTrue(StandardPage.objects.filter(pk=incomplete_folder.pk).exists())
        self.assertFalse(PackageFolderPage.objects.filter(pk=incomplete_folder.pk).exists())

    def test_second_apply_is_a_no_op(self):
        call_command("convert_legacy_detail_pages", "--apply")
        output = io.StringIO()

        call_command("convert_legacy_detail_pages", "--apply", stdout=output)

        self.assertIn("Converted 0 CMS pages.", output.getvalue())
        self.assertEqual(DestinationDetailPage.objects.count(), 1)
        self.assertEqual(PackageDetailPage.objects.count(), 1)


class ConvertSpecialPagesTests(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()
        # The command resolves the home page by slug; replace the default
        # Wagtail welcome page so slug "home" is unambiguous.
        Page.objects.filter(slug="home").delete()
        self.home = HomePage(title="Transaction home", slug="home")
        root.add_child(instance=self.home)

        self.enquiry = StandardPage(
            title="Enquiry", slug="enquiry", intro="Tell us about your trip"
        )
        self.home.add_child(instance=self.enquiry)

        self.contact = StandardPage(
            title="Contact Us", slug="contact", intro="Keep contact introduction"
        )
        self.home.add_child(instance=self.contact)
        self.privacy = StandardPage(
            title="Privacy Policy", slug="privacy", intro="Keep privacy introduction"
        )
        self.home.add_child(instance=self.privacy)

        self.checkout = StandardPage(title="Checkout", slug="checkout", intro="Obsolete intro")
        self.home.add_child(instance=self.checkout)
        self.success = StandardPage(title="Payment Success", slug="success")
        self.checkout.add_child(instance=self.success)

        # These block types are no longer part of the trimmed StandardPage
        # definition, so set the body as raw JSON to mimic production data the
        # converter must preserve without round-tripping through StreamField.
        self.bodies = {
            self.contact.pk: '[{"type": "lead_form", "value": {}, "id": "d4"}]',
            self.privacy.pk: '[{"type": "rich_text", "value": {}, "id": "e5"}]',
            self.enquiry.pk: '[{"type": "package_enquiry", "value": {}, "id": "a1"}]',
            self.checkout.pk: '[{"type": "checkout", "value": {}, "id": "b2"}]',
            self.success.pk: '[{"type": "payment_success", "value": {}, "id": "c3"}]',
        }
        for pk, body in self.bodies.items():
            StandardPage.objects.filter(pk=pk).update(body=body)

        self.enquiry_revision = self.enquiry.save_revision()
        self.contact_revision = self.contact.save_revision()
        self.privacy_revision = self.privacy.save_revision()
        self.checkout_revision = self.checkout.save_revision()
        self.success_revision = self.success.save_revision()

    def test_apply_converts_special_pages_and_rewrites_revisions(self):
        call_command("convert_transaction_pages", "--apply")

        contact = ContactPage.objects.get(pk=self.contact.pk)
        self.assertEqual(contact.intro, "Keep contact introduction")
        self.assertEqual(contact.url_path, "/home/contact/")
        self.assertEqual([b["type"] for b in contact.body.raw_data], ["lead_form"])

        privacy = PrivacyPage.objects.get(pk=self.privacy.pk)
        self.assertEqual(privacy.intro, "Keep privacy introduction")
        self.assertEqual(privacy.url_path, "/home/privacy/")
        self.assertEqual([b["type"] for b in privacy.body.raw_data], ["rich_text"])

        enquiry = EnquiryPage.objects.get(pk=self.enquiry.pk)
        self.assertEqual(enquiry.intro, "Tell us about your trip")
        self.assertEqual(enquiry.url_path, "/home/enquiry/")
        self.assertEqual([b["type"] for b in enquiry.body.raw_data], ["package_enquiry"])

        checkout = CheckoutPage.objects.get(pk=self.checkout.pk)
        self.assertEqual(checkout.url_path, "/home/checkout/")
        self.assertEqual([b["type"] for b in checkout.body.raw_data], ["checkout"])

        success = PaymentSuccessPage.objects.get(pk=self.success.pk)
        self.assertEqual(success.url_path, "/home/checkout/success/")
        self.assertEqual([b["type"] for b in success.body.raw_data], ["payment_success"])

        # The legacy StandardPage rows are gone for the converted pages.
        self.assertFalse(
            StandardPage.objects.filter(
                pk__in=[
                    self.contact.pk,
                    self.privacy.pk,
                    self.enquiry.pk,
                    self.checkout.pk,
                    self.success.pk,
                ]
            ).exists()
        )

        self.enquiry_revision.refresh_from_db()
        self.assertEqual(self.enquiry_revision.content_type, enquiry.content_type)
        self.assertEqual(self.enquiry_revision.content["intro"], "Tell us about your trip")
        self.assertIsInstance(self.enquiry_revision.as_object(), EnquiryPage)

        self.contact_revision.refresh_from_db()
        self.assertEqual(self.contact_revision.content_type, contact.content_type)
        self.assertEqual(self.contact_revision.content["intro"], "Keep contact introduction")
        self.assertIsInstance(self.contact_revision.as_object(), ContactPage)

        self.privacy_revision.refresh_from_db()
        self.assertEqual(self.privacy_revision.content_type, privacy.content_type)
        self.assertEqual(self.privacy_revision.content["intro"], "Keep privacy introduction")
        self.assertIsInstance(self.privacy_revision.as_object(), PrivacyPage)

        self.checkout_revision.refresh_from_db()
        self.assertEqual(self.checkout_revision.content_type, checkout.content_type)
        self.assertNotIn("intro", self.checkout_revision.content)
        self.assertIsInstance(self.checkout_revision.as_object(), CheckoutPage)

        self.success_revision.refresh_from_db()
        self.assertIsInstance(self.success_revision.as_object(), PaymentSuccessPage)

    def test_second_apply_is_a_no_op(self):
        call_command("convert_transaction_pages", "--apply")
        output = io.StringIO()

        call_command("convert_transaction_pages", "--apply", stdout=output)

        self.assertIn("Converted 0 CMS pages.", output.getvalue())
        self.assertEqual(ContactPage.objects.count(), 1)
        self.assertEqual(PrivacyPage.objects.count(), 1)
        self.assertEqual(EnquiryPage.objects.count(), 1)
        self.assertEqual(CheckoutPage.objects.count(), 1)
        self.assertEqual(PaymentSuccessPage.objects.count(), 1)
