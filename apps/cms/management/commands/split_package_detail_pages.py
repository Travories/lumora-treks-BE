"""Split legacy monolithic package bodies into screen-sized sections."""

import json
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page, Revision

from apps.cms.models import PackageDetailPage


SECTION_TYPES = (
    "package_header",
    "package_overview",
    "package_booking",
    "package_itinerary",
    "package_reviews",
)


def split_body(raw_body):
    """Replace each package template block while retaining surrounding blocks."""

    was_json = isinstance(raw_body, str)
    blocks = raw_body
    while isinstance(blocks, str):
        blocks = json.loads(blocks)
    changed = False
    result = []
    for block in blocks or []:
        if block.get("type") != "package_detail":
            result.append(block)
            continue

        changed = True
        value = block.get("value", {})
        legacy_settings = value.get("settings", {})
        for block_type in SECTION_TYPES:
            settings = {
                "anchor_id": block_type.replace("_", "-"),
                "background": legacy_settings.get("background", "default"),
                "spacing": "none",
                "container": legacy_settings.get("container", "default"),
                "hidden": legacy_settings.get("hidden", False),
            }
            section_value = {"settings": settings}
            if block_type == "package_booking":
                section_value["reserve_href"] = value.get("reserve_href", "")
            result.append(
                {
                    "type": block_type,
                    "value": section_value,
                    "id": str(uuid4()),
                }
            )
    transformed = json.dumps(result) if was_json else result
    return transformed, changed


class Command(BaseCommand):
    help = "Split package detail template blocks into five focused page sections."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Perform the conversion.")

    def handle(self, *args, **options):
        body_field = PackageDetailPage._meta.get_field("body")
        parent_link = PackageDetailPage._meta.get_ancestor_link(Page)
        pending = []

        with connection.cursor() as cursor:
            for page_id in PackageDetailPage.objects.values_list("pk", flat=True):
                cursor.execute(
                    f"SELECT {body_field.column} FROM {PackageDetailPage._meta.db_table} "
                    f"WHERE {parent_link.column} = %s",
                    [page_id],
                )
                row = cursor.fetchone()
                if not row:
                    continue
                transformed, changed = split_body(row[0])
                if changed:
                    pending.append((page_id, transformed))

        for page_id, _ in pending:
            self.stdout.write(f"package page: page {page_id} -> 5 screen sections")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to split."))
            return

        page_content_type = ContentType.objects.get_for_model(Page)
        with transaction.atomic():
            with connection.cursor() as cursor:
                for page_id, transformed in pending:
                    cursor.execute(
                        f"UPDATE {PackageDetailPage._meta.db_table} "
                        f"SET {body_field.column} = %s WHERE {parent_link.column} = %s",
                        [transformed, page_id],
                    )
                    changed_revisions = []
                    revisions = Revision.objects.filter(
                        base_content_type=page_content_type,
                        object_id=str(page_id),
                    )
                    for revision in revisions:
                        content = dict(revision.content)
                        transformed_revision, changed = split_body(content.get("body", "[]"))
                        if changed:
                            content["body"] = transformed_revision
                            revision.content = content
                            changed_revisions.append(revision)
                    if changed_revisions:
                        Revision.objects.bulk_update(changed_revisions, ["content"])

        self.stdout.write(self.style.SUCCESS(f"Split {len(pending)} package pages."))
