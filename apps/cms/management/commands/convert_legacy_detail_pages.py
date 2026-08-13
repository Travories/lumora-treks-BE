"""Convert legacy generic CMS detail pages to their dedicated page models.

The conversion preserves the Wagtail Page row, URL path, BasePage fields,
StreamField content, and revisions. Use without --apply to review changes.
"""

import json

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page

from apps.catalog.models import Destination, Package
from apps.cms.models import (
    DestinationDetailPage,
    DestinationIndexPage,
    PackageDetailPage,
    PackageFolderPage,
    PackageIndexPage,
    StandardPage,
)


class Command(BaseCommand):
    help = "Convert legacy StandardPage catalog URLs to dedicated Wagtail page models."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Perform the conversion.")

    def handle(self, *args, **options):
        apply = options["apply"]
        destination_index = StandardPage.objects.filter(slug="destinations").first()
        package_index = PackageIndexPage.objects.filter(slug="packages").first()
        if not destination_index or not package_index:
            self.stderr.write("Destination or package index page is missing; nothing converted.")
            return

        actions = []
        actions.append(("destination index", destination_index.pk, DestinationIndexPage, None))
        for page in destination_index.get_children().type(StandardPage):
            destination = Destination.objects.filter(slug=page.slug).first()
            if destination:
                actions.append(("destination detail", page.pk, DestinationDetailPage, destination.pk))

        for folder in package_index.get_children().type(StandardPage):
            package = Package.objects.filter(slug=folder.slug).first()
            if not package:
                continue
            actions.append(("package folder", folder.pk, PackageFolderPage, None))
            for detail in folder.get_children().type(StandardPage):
                if detail.slug == package.public_code:
                    actions.append(("package detail", detail.pk, PackageDetailPage, package.pk))

        for kind, page_id, model, related_id in actions:
            self.stdout.write(f"{kind}: page {page_id} -> {model.__name__}" + (f" ({related_id})" if related_id else ""))
        if not apply:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to convert."))
            return

        with transaction.atomic():
            for _, page_id, model, related_id in actions:
                page = Page.objects.get(pk=page_id)
                if page.content_type_id == ContentType.objects.get_for_model(model).pk:
                    continue
                # Page inheritance is flattened by Django migrations; derive
                # the generated parent-link name instead of assuming it.
                parent_link = model._meta.get_ancestor_link(Page)
                kwargs = {f"{parent_link.name}_id": page_id}
                if model is DestinationDetailPage:
                    kwargs["destination_id"] = related_id
                elif model is PackageDetailPage:
                    kwargs["package_id"] = related_id
                with connection.cursor() as cursor:
                    # Insert into only the newly introduced child table. Calling
                    # `save()` would validate the already-existing Page row as
                    # a new object and reject its inherited fields.
                    columns = [model._meta.get_field(parent_link.name).column]
                    values = [page_id]
                    if model is not PackageFolderPage:
                        legacy = StandardPage.objects.get(pk=page_id)
                        for field_name in ("body", "canonical_url", "noindex", "og_image_id"):
                            field = model._meta.get_field(field_name)
                            columns.append(field.column)
                            value = getattr(legacy, field_name)
                            if field_name == "body":
                                value = json.dumps(legacy._meta.get_field("body").get_prep_value(value))
                            values.append(value)
                    if model is DestinationDetailPage:
                        columns.append(model._meta.get_field("destination").column)
                        values.append(related_id)
                    elif model is PackageDetailPage:
                        columns.append(model._meta.get_field("package").column)
                        values.append(related_id)
                    placeholders = ", ".join(["%s"] * len(values))
                    cursor.execute(
                        f"INSERT INTO {model._meta.db_table} ({', '.join(columns)}) VALUES ({placeholders})",
                        values,
                    )
                    Page.objects.filter(pk=page_id).update(content_type=ContentType.objects.get_for_model(model))
                    # Delete only the legacy child-table record, never the shared Page/BasePage rows.
                    cursor.execute(
                        f"DELETE FROM {StandardPage._meta.db_table} WHERE {StandardPage._meta.get_ancestor_link(Page).column} = %s",
                        [page_id],
                    )
        self.stdout.write(self.style.SUCCESS(f"Converted {len(actions)} CMS pages."))
