"""Give existing blog posts a clear, screen-level Wagtail page outline."""

import json
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from wagtail.models import Page, Revision

from apps.cms.models import BlogPostPage


REQUIRED_TYPES = (
    "blog_article_header",
    "blog_article_body",
    "blog_related_stories",
    "cta_banner",
)


def section(block_type, **values):
    return {
        "type": block_type,
        "value": {
            **values,
            "settings": {
                "anchor_id": block_type.replace("blog_", "").replace("_", "-"),
                "background": "default",
                "spacing": "none",
                "container": "full",
                "hidden": False,
            },
        },
        "id": str(uuid4()),
    }


def organize_body(raw_body):
    """Insert missing article screens before any existing extra sections."""

    was_json = isinstance(raw_body, str)
    blocks = raw_body
    while isinstance(blocks, str):
        blocks = json.loads(blocks)
    blocks = blocks or []
    existing = {block.get("type") for block in blocks}
    missing = [block_type for block_type in REQUIRED_TYPES if block_type not in existing]
    if not missing:
        return raw_body, False

    defaults = {
        "blog_article_header": {},
        "blog_article_body": {},
        "blog_related_stories": {"heading": "Keep reading", "count": 3},
        "cta_banner": {
            "heading": "Create memories that stay with you long after the Journey Ends",
            "heading_highlight": "Journey",
            "text": "",
            "background_image": None,
            "buttons": [
                {
                    "label": "Reserve Now",
                    "link_type": "url",
                    "page": None,
                    "url": "/enquiry",
                    "anchor": "",
                    "document": None,
                    "email": "",
                    "phone": "",
                    "open_in_new_tab": False,
                    "style": "primary",
                    "size": "md",
                    "icon": "",
                }
            ],
        },
    }
    existing_required = {
        block.get("type"): block for block in blocks if block.get("type") in REQUIRED_TYPES
    }
    organized = [
        existing_required.get(block_type) or section(block_type, **defaults[block_type])
        for block_type in REQUIRED_TYPES
    ]
    organized.extend(block for block in blocks if block.get("type") not in REQUIRED_TYPES)
    return (json.dumps(organized) if was_json else organized), True


class Command(BaseCommand):
    help = "Organize blog posts into header, article, related-stories and CTA sections."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Perform the conversion.")

    def handle(self, *args, **options):
        body_field = BlogPostPage._meta.get_field("body")
        parent_link = BlogPostPage._meta.get_ancestor_link(Page)
        pending = []

        with connection.cursor() as cursor:
            for page_id in BlogPostPage.objects.values_list("pk", flat=True):
                cursor.execute(
                    f"SELECT {body_field.column} FROM {BlogPostPage._meta.db_table} "
                    f"WHERE {parent_link.column} = %s",
                    [page_id],
                )
                row = cursor.fetchone()
                if not row:
                    continue
                organized, changed = organize_body(row[0])
                if changed:
                    pending.append((page_id, organized))

        for page_id, _ in pending:
            self.stdout.write(f"blog post: page {page_id} -> 3 article screens + extras")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to organize."))
            return

        page_content_type = ContentType.objects.get_for_model(Page)
        with transaction.atomic():
            with connection.cursor() as cursor:
                for page_id, organized in pending:
                    cursor.execute(
                        f"UPDATE {BlogPostPage._meta.db_table} "
                        f"SET {body_field.column} = %s WHERE {parent_link.column} = %s",
                        [organized, page_id],
                    )
                    changed_revisions = []
                    revisions = Revision.objects.filter(
                        base_content_type=page_content_type,
                        object_id=str(page_id),
                    )
                    for revision in revisions:
                        content = dict(revision.content)
                        organized_revision, changed = organize_body(content.get("body", "[]"))
                        if changed:
                            content["body"] = organized_revision
                            revision.content = content
                            changed_revisions.append(revision)
                    if changed_revisions:
                        Revision.objects.bulk_update(changed_revisions, ["content"])

        self.stdout.write(self.style.SUCCESS(f"Organized {len(pending)} blog posts."))
