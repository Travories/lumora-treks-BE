"""Split legacy monolithic destination bodies into screen-sized sections."""

import json
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page, Revision

from apps.cms.models import DestinationDetailPage


SECTION_TYPES = (
    "destination_header",
    "destination_overview",
    "destination_packages",
)


def split_body(raw_body):
    """Replace each legacy destination template block, preserving its position."""

    was_json = isinstance(raw_body, str)
    blocks = raw_body
    # JSONField queryset updates can leave legacy StreamField data wrapped in
    # an extra JSON string. Accept both shapes so recovery is deterministic.
    while isinstance(blocks, str):
        blocks = json.loads(blocks)
    changed = False
    result = []
    for block in blocks or []:
        if block.get("type") != "destination_detail":
            result.append(block)
            continue

        changed = True
        legacy_settings = block.get("value", {}).get("settings", {})
        for block_type in SECTION_TYPES:
            settings = {
                "anchor_id": block_type.replace("_", "-"),
                "background": legacy_settings.get("background", "default"),
                "spacing": "none",
                "container": legacy_settings.get("container", "default"),
                "hidden": legacy_settings.get("hidden", False),
            }
            result.append(
                {
                    "type": block_type,
                    "value": {"settings": settings},
                    "id": str(uuid4()),
                }
            )
    transformed = json.dumps(result) if was_json else result
    return transformed, changed


class Command(BaseCommand):
    help = "Split destination detail template blocks into Header, Overview and Packages sections."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Perform the conversion.")

    def handle(self, *args, **options):
        body_field = DestinationDetailPage._meta.get_field("body")
        parent_link = DestinationDetailPage._meta.get_ancestor_link(Page)
        page_ids = list(DestinationDetailPage.objects.values_list("pk", flat=True))
        pending = []

        with connection.cursor() as cursor:
            for page_id in page_ids:
                cursor.execute(
                    f"SELECT {body_field.column} FROM {DestinationDetailPage._meta.db_table} "
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
            self.stdout.write(f"destination page: page {page_id} -> 3 screen sections")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to split."))
            return

        page_content_type = ContentType.objects.get_for_model(Page)
        with transaction.atomic():
            with connection.cursor() as cursor:
                for page_id, transformed in pending:
                    cursor.execute(
                        f"UPDATE {DestinationDetailPage._meta.db_table} "
                        f"SET {body_field.column} = %s WHERE {parent_link.column} = %s",
                        [transformed, page_id],
                    )
                    revisions = Revision.objects.filter(
                        base_content_type=page_content_type,
                        object_id=str(page_id),
                    )
                    changed_revisions = []
                    for revision in revisions:
                        content = dict(revision.content)
                        transformed_revision, changed = split_body(content.get("body", "[]"))
                        if changed:
                            content["body"] = transformed_revision
                            revision.content = content
                            changed_revisions.append(revision)
                    if changed_revisions:
                        Revision.objects.bulk_update(changed_revisions, ["content"])

        self.stdout.write(self.style.SUCCESS(f"Split {len(pending)} destination pages."))
