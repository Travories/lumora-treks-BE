"""Seed the live, CMS-editable destinations behind Lumora's current packages."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Destination, Package
from apps.core.models import CustomImage


DESTINATIONS = {
    "annapurna-circuit": {
        "title": "Annapurna Circuit", "image": "Pkg Annapurna", "subtitle": "A legendary Himalayan journey through changing valleys and high passes.",
        "description": "The Annapurna Circuit moves from subtropical river valleys into dry Himalayan landscapes, passing traditional villages and dramatic mountain walls. It is best known for the high Thorong La crossing and the variety of culture and scenery along the route.",
        "highlights": ["Diverse landscapes from low valleys to high Himalaya", "Traditional villages and mountain culture", "Thorong La pass trekking route"], "best_season": "March to May and October to November", "layout": "large", "packages": [],
    },
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
    "bandipur": {
        "title": "Bandipur", "image": "Region Bandipur", "subtitle": "A preserved hill town with Newari character and Himalayan views.",
        "description": "Bandipur sits on a ridge between Kathmandu and Pokhara, with pedestrian lanes, traditional Newari houses, and wide views toward the Annapurna range. It is a peaceful stop for culture, short walks, and slower travel.",
        "highlights": ["Historic Newari townscape", "Ridge-top Himalayan views", "Relaxed walking and local cafés"], "best_season": "February to May and October to December", "layout": "small", "packages": [],
    },
    "kathmandu": {
        "title": "Kathmandu", "image": "Region Kathmandu", "subtitle": "Living heritage, busy bazaars, and a gateway to Nepal.",
        "description": "Kathmandu brings together historic squares, Buddhist stupas, Hindu temples, workshops, and vibrant neighbourhoods. It is the natural starting point for most journeys in Nepal and rewards time beyond the airport transfer.",
        "highlights": ["UNESCO heritage sites and living temples", "Food, crafts, and local neighbourhoods", "Gateway for journeys across Nepal"], "best_season": "February to May and October to December", "layout": "small", "packages": [],
    },
    "swayambhunath": {
        "title": "Swayambhunath", "image": "Region Swayambhunath", "subtitle": "An ancient hilltop stupa overlooking the Kathmandu Valley.",
        "description": "Swayambhunath, often called the Monkey Temple, is one of the Kathmandu Valley's most recognisable sacred sites. Its white dome, watchful Buddha eyes, prayer flags, and hilltop views make it a memorable cultural stop.",
        "highlights": ["Ancient Buddhist stupa", "Panoramic Kathmandu Valley views", "Prayer flags, shrines, and local life"], "best_season": "Year-round; clearest views October to March", "layout": "small", "packages": [],
    },
    "everest-region": {
        "title": "Everest Region", "image": "Region Everest", "subtitle": "High Himalayan trails beneath the world's tallest mountains.",
        "description": "The Everest region is shaped by Sherpa culture, suspension bridges, alpine valleys, and iconic views of Everest, Lhotse, and Ama Dablam. Routes range from village stays to demanding high-altitude expeditions.",
        "highlights": ["Everest and Ama Dablam mountain views", "Sherpa villages and monasteries", "World-class high-altitude trekking"], "best_season": "March to May and October to November", "layout": "large", "packages": [],
    },
    "dhorpatan-region": {
        "title": "Dhorpatan Region", "image": "Experience Dhorpatan", "subtitle": "Remote valleys, alpine meadows, and western Nepal wilderness.",
        "description": "Dhorpatan offers a quieter side of Nepal, with high pasturelands, traditional settlements, and wide-open trails in the western hills. It suits travellers seeking a less-travelled mountain landscape.",
        "highlights": ["Remote western Nepal trails", "Alpine meadows and forest", "Traditional hill communities"], "best_season": "March to May and October to November", "layout": "small", "packages": [],
    },
    "patan": {
        "title": "Patan", "image": "Experience Patan", "subtitle": "Newari artistry, courtyards, and one of Nepal's finest durbar squares.",
        "description": "Patan is celebrated for its dense concentration of temples, stonework, metal craft, and traditional Newari courtyards. Its compact historic centre makes it ideal for a thoughtful cultural day in the valley.",
        "highlights": ["Patan Durbar Square", "Newari art and metalwork", "Walkable historic courtyards"], "best_season": "Year-round; October to March is especially clear", "layout": "small", "packages": [],
    },
    "pokhara": {
        "title": "Pokhara", "image": "Experience Pokhara", "subtitle": "Lakeside calm with the Annapurna range on the horizon.",
        "description": "Pokhara balances Phewa Lake, easy-going cafés, mountain viewpoints, and access to the Annapurna trails. It works equally well as a restorative stop and as the launch point for adventure in western Nepal.",
        "highlights": ["Phewa Lake and lakeside life", "Annapurna and Machhapuchhre views", "Gateway to trekking and adventure"], "best_season": "February to May and October to December", "layout": "large", "packages": [],
    },
    "journey-to-fish-lake": {
        "title": "Journey to Fish Lake", "image": "Seasonal 1", "subtitle": "A quieter escape to remote lakeside landscapes.",
        "description": "This destination represents a slower journey through Nepal's remote lake country, where the reward is open water, birdlife, and time away from busy routes. It is a natural match for travellers who value pace and scenery.",
        "highlights": ["Remote lake landscapes", "Quiet walking routes", "Birdlife and wide views"], "best_season": "April to June and September to November", "layout": "tall", "packages": [],
    },
    "gosaikunda-trail": {
        "title": "Gosaikunda Trail", "image": "Seasonal 2", "subtitle": "A sacred alpine lake trek north of Kathmandu.",
        "description": "The Gosaikunda Trail climbs through Langtang National Park to a cluster of high, sacred lakes. The route combines forest, ridges, Tamang culture, and an unforgettable alpine destination.",
        "highlights": ["Sacred high-altitude lakes", "Langtang National Park trails", "Tamang villages and ridge views"], "best_season": "March to May and October to November", "layout": "tall", "packages": [],
    },
    "chitwan-safari": {
        "title": "Chitwan Safari", "image": "Seasonal 3", "subtitle": "Jungle walks and river landscapes in Nepal's southern lowlands.",
        "description": "Chitwan National Park offers a different side of Nepal: sal forest, grassland, rivers, and rich wildlife. Guided nature activities focus on responsible viewing, local Tharu culture, and time outdoors.",
        "highlights": ["Guided jungle and river activities", "Wildlife and birdwatching", "Tharu culture and lowland landscapes"], "best_season": "October to March", "layout": "wide", "packages": [],
    },
    "mustang-valley": {
        "title": "Mustang Valley", "image": "Seasonal 4", "subtitle": "Wind-shaped cliffs, ancient settlements, and trans-Himalayan culture.",
        "description": "Mustang feels distinct from the greener parts of Nepal, with dry valleys, eroded cliffs, walled villages, and Tibetan-influenced culture. The journey is as much about the road and landscape as the destination.",
        "highlights": ["Trans-Himalayan desert scenery", "Ancient walled settlements", "Tibetan-influenced culture"], "best_season": "May to October", "layout": "tall", "packages": [],
    },
    "langtang-valley": {
        "title": "Langtang Valley", "image": "Seasonal 5", "subtitle": "A close-to-Kathmandu Himalayan valley of forest, peaks, and Tamang culture.",
        "description": "Langtang Valley offers an accessible Himalayan trekking experience with oak and rhododendron forest, yak pastures, glacier views, and warm Tamang hospitality. It is ideal for travellers with limited time.",
        "highlights": ["Himalayan trekking close to Kathmandu", "Tamang villages and culture", "Forest, pasture, and glacier views"], "best_season": "March to May and October to November", "layout": "tall", "packages": [],
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
