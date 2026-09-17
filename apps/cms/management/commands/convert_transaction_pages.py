"""Convert special StandardPage routes to their dedicated models.

Contact, Privacy, Enquiry, Checkout and Payment success were originally
StandardPage instances. This gives each a dedicated, restricted page model
while preserving the Wagtail Page row, URL path, BasePage fields, StreamField
content and revisions. Use without --apply to review changes.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page, Revision

from apps.cms.models import (
    CheckoutPage,
    ContactPage,
    EnquiryPage,
    HomePage,
    PaymentSuccessPage,
    PrivacyPage,
    StandardPage,
)


class Command(BaseCommand):
    help = "Convert special StandardPage routes to dedicated Wagtail page models."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Perform the conversion.")

    def handle(self, *args, **options):
        apply = options["apply"]
        # Resolve home by type, not slug: production's home slug is "home-real",
        # so a hardcoded slug="home" lookup finds nothing and converts nothing.
        # This mirrors how seed_lumora locates the home page.
        home = HomePage.objects.first()
        if not home:
            self.stderr.write("Home page is missing; nothing converted.")
            return

        # (slug, parent_page, target_model). The success page nests under
        # checkout so it is resolved relative to the checkout page, not home.
        checkout = home.get_children().filter(slug="checkout").first()
        candidates = [
            ("contact", home, ContactPage),
            ("privacy", home, PrivacyPage),
            ("enquiry", home, EnquiryPage),
            ("checkout", home, CheckoutPage),
        ]
        if checkout:
            candidates.append(("success", checkout, PaymentSuccessPage))

        actions = []
        for slug, parent, model in candidates:
            page = parent.get_children().filter(slug=slug).first()
            if not page:
                continue
            if page.content_type_id not in self._content_type_ids(StandardPage, model):
                continue
            actions.append((page.pk, model))

        for page_id, model in actions:
            self.stdout.write(f"special page: page {page_id} -> {model.__name__}")
        if not apply:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to convert."))
            return

        converted = 0
        with transaction.atomic():
            for page_id, model in actions:
                page = Page.objects.get(pk=page_id)
                target_content_type = ContentType.objects.get_for_model(model)
                model_has_intro = any(field.name == "intro" for field in model._meta.fields)
                if page.content_type_id == target_content_type.pk:
                    # Re-normalise revisions, making the command safe to resume.
                    self._migrate_revisions(page_id, target_content_type, model_has_intro)
                    continue
                # Page inheritance is flattened by Django migrations; derive
                # the generated parent-link name instead of assuming it.
                parent_link = model._meta.get_ancestor_link(Page)
                legacy = StandardPage.objects.get(pk=page_id)
                field_names = ["canonical_url", "noindex", "og_image"]
                # Page types with an editorial introduction keep it.
                if model_has_intro:
                    field_names.append("intro")
                columns = [model._meta.get_field(parent_link.name).column]
                values = [page_id]
                for field_name in field_names:
                    field = model._meta.get_field(field_name)
                    columns.append(field.column)
                    values.append(getattr(legacy, field.attname))
                # Copy the body as raw JSON text straight from the legacy table.
                # Round-tripping through the StandardPage StreamField would drop
                # any block type no longer in its (now trimmed) definition.
                columns.append(model._meta.get_field("body").column)
                values.append(self._raw_body(page_id))
                placeholders = ", ".join(["%s"] * len(values))
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT 1 FROM {model._meta.db_table} "
                        f"WHERE {model._meta.get_field(parent_link.name).column} = %s",
                        [page_id],
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            f"INSERT INTO {model._meta.db_table} ({', '.join(columns)}) VALUES ({placeholders})",
                            values,
                        )
                    Page.objects.filter(pk=page_id).update(content_type=target_content_type)
                    self._migrate_revisions(page_id, target_content_type, model_has_intro)
                    # Delete only the legacy child-table record, never the shared Page/BasePage rows.
                    cursor.execute(
                        f"DELETE FROM {StandardPage._meta.db_table} "
                        f"WHERE {StandardPage._meta.get_ancestor_link(Page).column} = %s",
                        [page_id],
                    )
                converted += 1
        self.stdout.write(self.style.SUCCESS(f"Converted {converted} CMS pages."))

    @staticmethod
    def _content_type_ids(*models):
        return {ContentType.objects.get_for_model(model).pk for model in models}

    @staticmethod
    def _raw_body(page_id):
        """Return the untouched body JSON text from the legacy StandardPage row."""

        body_column = StandardPage._meta.get_field("body").column
        pk_column = StandardPage._meta.get_ancestor_link(Page).column
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {body_column} FROM {StandardPage._meta.db_table} WHERE {pk_column} = %s",
                [page_id],
            )
            return cursor.fetchone()[0]

    @staticmethod
    def _migrate_revisions(page_id, target_content_type, model_has_intro):
        """Point page revisions at the new concrete model and fix their payload."""

        page_content_type = ContentType.objects.get_for_model(Page)
        revisions = Revision.objects.filter(
            base_content_type=page_content_type,
            object_id=str(page_id),
        )
        changed = []
        for revision in revisions:
            content = dict(revision.content)
            content["content_type"] = target_content_type.pk
            if not model_has_intro:
                content.pop("intro", None)
            revision.content_type = target_content_type
            revision.content = content
            changed.append(revision)
        if changed:
            Revision.objects.bulk_update(changed, ["content_type", "content"])
