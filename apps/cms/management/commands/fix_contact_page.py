"""Restore the enquiry form to the `/contact` page.

The Contact page body is CMS-managed, and on some environments it has drifted
so that the `contact_form` block (→ `ContactForm.tsx`, the "Leave your message"
enquiry form) is missing — e.g. prod ended up with only a `faq` block, so the
frontend rendered Navbar → FAQ → Footer with no form at all.

This command normalises the body to the canonical structure:

    contact_hero → contact_form → <any other existing blocks, e.g. faq>

It is idempotent and safe to re-run: existing hero/form blocks (including the
generic `page_hero`/`lead_form` variants) are dropped and rebuilt, while every
other block (the FAQ and anything else authored in Wagtail) is preserved in
order. Run it wherever the CMS database lives:

    python manage.py fix_contact_page            # apply + publish
    python manage.py fix_contact_page --dry-run  # show the plan, change nothing
"""

from django.core.management.base import BaseCommand
from wagtail.images import get_image_model

from apps.cms.models import ContactPage

# Hero/form blocks we own and rebuild; everything else in the body is kept.
HERO_TYPES = {"contact_hero", "page_hero"}
FORM_TYPES = {"contact_form", "lead_form"}
REBUILT_TYPES = HERO_TYPES | FORM_TYPES


def _settings(anchor_id="", background="default", spacing="md", container="default"):
    return {
        "anchor_id": anchor_id,
        "background": background,
        "spacing": spacing,
        "container": container,
        "hidden": False,
    }


class Command(BaseCommand):
    help = "Restore the ContactForm (enquiry form) block to the /contact page."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the planned body without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        page = ContactPage.objects.first()
        if page is None:
            self.stderr.write(self.style.ERROR("No ContactPage found — nothing to fix."))
            return

        before = [b.block_type for b in page.body]
        self.stdout.write(f"ContactPage id={page.id} current body: {before}")

        # Preserve every block that isn't a hero/form we're about to rebuild.
        preserved = [
            (b.block_type, b.value)
            for b in page.body
            if b.block_type not in REBUILT_TYPES
        ]

        # The Figma contact hero requires an image; prefer the seeded one.
        Image = get_image_model()
        hero_image = (
            Image.objects.filter(title__icontains="contact hero").first()
            or Image.objects.first()
        )

        new_body = []
        if hero_image is not None:
            new_body.append(
                (
                    "contact_hero",
                    {"image": hero_image, "settings": _settings("contact-hero")},
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No image available — skipping contact_hero (form still added)."
                )
            )

        new_body.append(
            (
                "contact_form",
                {
                    "heading": "Don't Hesitate to Contact Us",
                    "heading_highlight": "Contact Us",
                    "description": "Whether you have a quick question or want to book a full consultation — we're easy to reach. Fill in the form and we'll respond within one business day",
                    "description_highlight": "Fill in the form and we'll respond within one business day",
                    "socials": [],
                    "destinations": [],
                    "submit_label": "Reserve Now",
                    "settings": _settings("contact-form"),
                    # NB: `form_key` is NOT a CMS field on ContactFormBlock — the
                    # frontend hardcodes form_key="contact" in ContactForm.tsx.
                },
            )
        )
        new_body.extend(preserved)

        after = [t for t, _ in new_body]
        self.stdout.write(f"Planned body: {after}")

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: no changes saved."))
            return

        page.body = new_body
        revision = page.save_revision()
        revision.publish()
        self.stdout.write(self.style.SUCCESS("Contact page updated and published."))
