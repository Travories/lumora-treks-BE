"""Convert legacy generic CMS detail pages to their dedicated page models.

The conversion preserves the Wagtail Page row, URL path, BasePage fields,
StreamField content, and revisions. Use without --apply to review changes.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page, Revision

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
        destination_index = Page.objects.filter(slug="destinations").first()
        package_index = PackageIndexPage.objects.filter(slug="packages").first()
        if not destination_index or not package_index:
            self.stderr.write("Destination or package index page is missing; nothing converted.")
            return

        actions = []
        if destination_index.content_type_id in self._content_type_ids(StandardPage, DestinationIndexPage):
            actions.append(("destination index", destination_index.pk, DestinationIndexPage, None))
        for page in destination_index.get_children():
            if page.content_type_id not in self._content_type_ids(StandardPage, DestinationDetailPage):
                continue
            destination = Destination.objects.filter(slug=page.slug).first()
            if destination:
                actions.append(("destination detail", page.pk, DestinationDetailPage, destination.pk))

        for folder in package_index.get_children():
            if folder.content_type_id not in self._content_type_ids(StandardPage, PackageFolderPage):
                continue
            package = Package.objects.filter(slug=folder.slug).first()
            if not package:
                continue
            detail = folder.get_children().filter(slug=package.public_code).first()
            # A folder and its code-addressed detail are one conversion unit. Do
            # not strand a converted folder when either half is missing/wrong.
            if not detail or detail.content_type_id not in self._content_type_ids(
                StandardPage, PackageDetailPage
            ):
                continue
            actions.append(("package folder", folder.pk, PackageFolderPage, None))
            actions.append(("package detail", detail.pk, PackageDetailPage, package.pk))

        for kind, page_id, model, related_id in actions:
            self.stdout.write(f"{kind}: page {page_id} -> {model.__name__}" + (f" ({related_id})" if related_id else ""))
        if not apply:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to convert."))
            return

        converted = 0
        with transaction.atomic():
            for _, page_id, model, related_id in actions:
                page = Page.objects.get(pk=page_id)
                target_content_type = ContentType.objects.get_for_model(model)
                if page.content_type_id == target_content_type.pk:
                    # Re-normalise revisions as well, which makes the command
                    # safe to resume after a partially completed older run.
                    self._migrate_revisions(page_id, model, related_id, target_content_type)
                    continue
                # Page inheritance is flattened by Django migrations; derive
                # the generated parent-link name instead of assuming it.
                parent_link = model._meta.get_ancestor_link(Page)
                with connection.cursor() as cursor:
                    # Insert into only the newly introduced child table. Calling
                    # `save()` would validate the already-existing Page row as
                    # a new object and reject its inherited fields.
                    columns = [model._meta.get_field(parent_link.name).column]
                    values = [page_id]
                    if model is not PackageFolderPage:
                        legacy = StandardPage.objects.get(pk=page_id)
                        field_names = ["body", "canonical_url", "noindex", "og_image"]
                        # DestinationIndexPage intentionally retains the
                        # editorial introduction from the generic index page.
                        if model is DestinationIndexPage and any(
                            field.name == "intro" for field in model._meta.fields
                        ):
                            field_names.append("intro")
                        for field_name in field_names:
                            field = model._meta.get_field(field_name)
                            columns.append(field.column)
                            # Copy StreamField JSON directly. A legacy block
                            # may no longer exist in StandardPage's narrowed
                            # runtime definition after all migrations run.
                            value = (
                                self._raw_standard_body(page_id)
                                if field_name == "body"
                                else getattr(legacy, field.attname)
                            )
                            values.append(value)
                    if model is DestinationDetailPage:
                        columns.append(model._meta.get_field("destination").column)
                        values.append(related_id)
                    elif model is PackageDetailPage:
                        columns.append(model._meta.get_field("package").column)
                        values.append(related_id)
                    placeholders = ", ".join(["%s"] * len(values))
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
                    self._migrate_revisions(page_id, model, related_id, target_content_type)
                    # Delete only the legacy child-table record, never the shared Page/BasePage rows.
                    cursor.execute(
                        f"DELETE FROM {StandardPage._meta.db_table} WHERE {StandardPage._meta.get_ancestor_link(Page).column} = %s",
                        [page_id],
                    )
                converted += 1
        self.stdout.write(self.style.SUCCESS(f"Converted {converted} CMS pages."))

    @staticmethod
    def _content_type_ids(*models):
        return {ContentType.objects.get_for_model(model).pk for model in models}

    @staticmethod
    def _raw_standard_body(page_id):
        body_field = StandardPage._meta.get_field("body")
        parent_link = StandardPage._meta.get_ancestor_link(Page)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {body_field.column} FROM {StandardPage._meta.db_table} "
                f"WHERE {parent_link.column} = %s",
                [page_id],
            )
            return cursor.fetchone()[0]

    @staticmethod
    def _migrate_revisions(page_id, model, related_id, target_content_type):
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
            if model is DestinationDetailPage:
                content["destination"] = related_id
                content.pop("intro", None)
            elif model is PackageDetailPage:
                content["package"] = related_id
                content.pop("intro", None)
            revision.content_type = target_content_type
            revision.content = content
            changed.append(revision)
        if changed:
            Revision.objects.bulk_update(changed, ["content_type", "content"])
