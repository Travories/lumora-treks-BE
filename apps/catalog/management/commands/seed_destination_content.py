"""Seed the live, CMS-editable destinations behind Lumora's current packages."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Destination, Package
from apps.core.models import CustomImage


DESTINATIONS = {
    "annapurna-region": {
        "title": "Annapurna Region",
        "image": "Region Annapurna",
        "subtitle": "Teahouse trails, Gurung villages, and the Annapurna Sanctuary.",
        "description": "The Annapurna region combines welcoming mountain villages with some of Nepal's most rewarding Himalayan walking. Travel through rhododendron forest and stone settlements toward wide views of Machhapuchhre, Annapurna South, and the sanctuary.",
        "highlights": ["Annapurna Base Camp at 4,130 m", "Gurung villages and local teahouses", "Forest trails and Himalayan panoramas"],
        "best_season": "March to May and October to November",
        "layout": "large",
        "packages": ["annapurna-base-camp-trek", "abc-base-camp-trek"],
    },
    "poon-hill": {
        "title": "Poon Hill",
        "image": "Dest Poonhills",
        "subtitle": "A compact Annapurna trek for a remarkable Himalayan sunrise.",
        "description": "Poon Hill is a classic short trek above Ghorepani. Its pre-dawn viewpoint opens across Dhaulagiri, Annapurna South, Hiunchuli, and Machhapuchhre, with village trails and rhododendron forest along the way.",
        "highlights": ["Sunrise panorama from Poon Hill", "Ghorepani village and teahouses", "Rhododendron forest trails"],
        "best_season": "March to May and October to November",
        "layout": "small",
        "packages": ["poon-hill-sunrise-trek"],
    },
    "rara-lake": {
        "title": "Rara Lake",
        "image": "Region Rara Lake",
        "subtitle": "Quiet water, far-west hills, and Nepal's largest alpine lake.",
        "description": "Rara Lake National Park rewards the journey west with deep-blue water, forested slopes, and a calmer rhythm than Nepal's busier trekking corridors. It is ideal for lakeside walks, birdlife, and wide open viewpoints.",
        "highlights": ["Nepal's largest alpine lake", "Lakeside walks and viewpoints", "Birdlife and far-west landscapes"],
        "best_season": "April to June and September to November",
        "layout": "small",
        "packages": ["journey-to-fish-lake"],
    },
    "kathmandu-pokhara": {
        "title": "Kathmandu & Pokhara",
        "image": "Experience Pokhara",
        "subtitle": "Living heritage in Kathmandu, followed by Pokhara's lakeside calm.",
        "description": "This route connects Kathmandu's historic squares and living temples with Pokhara's relaxed lakefront and mountain views. It is designed for travelers who want a balanced first journey through Nepal without a high-altitude trek.",
        "highlights": ["Kathmandu's heritage sites", "Phewa Lake and Pokhara viewpoints", "Private transfers and local guidance"],
        "best_season": "February to May and October to December",
        "layout": "small",
        "packages": ["pokhara-kathmandu-tours"],
    },
}


class Command(BaseCommand):
    help = "Upsert CMS destinations and link Lumora's active packages to them."

    @transaction.atomic
    def handle(self, *args, **options):
        image_by_title = {image.title: image for image in CustomImage.objects.filter(title__in={content["image"] for content in DESTINATIONS.values()})}
        missing_images = [content["image"] for content in DESTINATIONS.values() if content["image"] not in image_by_title]
        if missing_images:
            raise CommandError(f'Missing CMS image(s): {", ".join(sorted(missing_images))}.')

        existing = {destination.slug: destination for destination in Destination.objects.filter(slug__in=DESTINATIONS)}
        new_destinations = []
        for order, (slug, content) in enumerate(DESTINATIONS.items()):
            values = {
                "title": content["title"], "image_id": image_by_title[content["image"]].pk,
                "subtitle": content["subtitle"], "description": content["description"],
                "highlights": "\n".join(content["highlights"]), "region": content["title"],
                "best_season": content["best_season"], "default_layout": content["layout"],
                "is_featured": True, "sort_order": order,
            }
            if slug in existing:
                Destination.objects.filter(pk=existing[slug].pk).update(**values)
            else:
                new_destinations.append(Destination(slug=slug, **values))
        Destination.objects.bulk_create(new_destinations)
        destinations = {destination.slug: destination for destination in Destination.objects.filter(slug__in=DESTINATIONS)}

        linked_slugs = set()
        for slug, content in DESTINATIONS.items():
            destination = destinations[slug]
            packages = list(Package.objects.filter(slug__in=content["packages"]))
            found_slugs = {package.slug for package in packages}
            missing = set(content["packages"]) - found_slugs
            if missing:
                raise CommandError(f'Missing package(s): {", ".join(sorted(missing))}.')
            for package in packages:
                linked_slugs.add(package.slug)
            Package.objects.filter(pk__in=[package.pk for package in packages]).update(destination=destination)
            self.stdout.write(f'Updated {destination.title} ({len(packages)} linked package(s))')

        Package.objects.filter(is_active=True).exclude(slug__in=linked_slugs).update(destination=None)
        Destination.objects.exclude(pk__in=[destination.pk for destination in destinations.values()]).update(is_featured=False)
        self.stdout.write(self.style.SUCCESS(f"Linked {len(linked_slugs)} active package(s) to CMS destinations."))
