"""Seed complete, package-specific details for Lumora's initial catalogue."""

from io import BytesIO
from urllib.request import Request, urlopen

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Package, PackageGalleryImage, PackageHighlight, PackageIncludedItem, PackageItineraryDay
from apps.core.models import CustomImage


COMMONS_ANNAPURNA = "https://upload.wikimedia.org/wikipedia/commons/5/52/Tourists_trekking_in_Annapurna_region.jpg"

PACKAGES = {
    "annapurna-base-camp-trek": {
        "summary": "A classic teahouse trek through Gurung villages, forest trails, and the Annapurna Sanctuary.",
        "description": "Follow the Modi Khola valley from the foothills into the Annapurna Sanctuary. This seven-day route balances a steady ascent with warm teahouse stays, rhododendron forest, Machhapuchhre views, and a dawn at Annapurna Base Camp (4,130 m).",
        "duration": "7 Days", "duration_days": 7, "price": 650, "difficulty": "moderate", "people_count": 12,
        "highlights": ["Sunrise at Annapurna Base Camp", "Gurung villages and teahouse hospitality", "Machhapuchhre and Annapurna Sanctuary views"],
        "itinerary": [
            ("Day 1", "Pokhara to Ghandruk", "Drive from Pokhara to the trailhead and walk into Ghandruk, a stone village with wide views of Annapurna South."),
            ("Day 2", "Ghandruk to Chhomrong", "Descend to the Kimrong Khola, then climb to Chhomrong, the gateway village to the sanctuary."),
            ("Day 3", "Chhomrong to Bamboo", "Follow stone steps and a shaded forest trail through Sinuwa, Kuldighar, and Bamboo."),
            ("Day 4", "Bamboo to Deurali", "Climb through bamboo and rhododendron forest to the open valley below Machhapuchhre Base Camp."),
            ("Day 5", "Deurali to Annapurna Base Camp", "Walk beneath the steep sanctuary walls to Annapurna Base Camp for an evening among the peaks."),
            ("Day 6", "Annapurna Base Camp to Bamboo", "Enjoy a clear mountain morning, then retrace the valley downhill to Bamboo."),
            ("Day 7", "Bamboo to Pokhara", "Descend to the roadhead and return to Pokhara after the trek."),
        ],
    },
    "poon-hill-sunrise-trek": {
        "summary": "A short, rewarding Annapurna trek built around the sunrise panorama from Poon Hill.",
        "description": "This compact four-day trek passes through Magar and Gurung villages, rhododendron forest, and traditional teahouses before an early climb to Poon Hill. The viewpoint looks across Dhaulagiri, Annapurna South, Hiunchuli, and Machhapuchhre.",
        "duration": "4 Days", "duration_days": 4, "price": 380, "difficulty": "easy", "people_count": 12,
        "highlights": ["Sunrise from Poon Hill", "Ghorepani's mountain teahouses", "Rhododendron forest and village trails"],
        "itinerary": [
            ("Day 1", "Pokhara to Ulleri", "Drive to Nayapul and walk past terraced fields to Ulleri."),
            ("Day 2", "Ulleri to Ghorepani", "Climb through forest to Ghorepani, a lively stop on the Annapurna trails."),
            ("Day 3", "Poon Hill sunrise and Tadapani", "Make the pre-dawn walk to Poon Hill, then continue through forest to Tadapani."),
            ("Day 4", "Tadapani to Pokhara", "Descend through Ghandruk and return by road to Pokhara."),
        ],
    },
    "journey-to-fish-lake": {
        "summary": "A relaxed highland escape to Rara Lake, Nepal's largest alpine lake.",
        "description": "Travel from Nepalgunj into the far-west hills for quiet trails, lakeside viewpoints, and time around the deep-blue waters of Rara Lake. This is a slower journey for travelers who want scenery, birdlife, and space away from busy trekking routes.",
        "duration": "5 Days", "duration_days": 5, "price": 720, "difficulty": "easy", "people_count": 10,
        "highlights": ["Rara Lake shoreline walks", "Far-west Nepal landscapes", "Birdwatching and quiet viewpoints"],
        "itinerary": [("Day 1", "Nepalgunj to Talcha", "Fly to Talcha and transfer toward Rara National Park."), ("Day 2", "Explore Rara Lake", "Walk the shoreline and settle into the lake landscape."), ("Day 3", "Lakeside viewpoints", "Hike to a viewpoint for broad views across Rara and the surrounding hills."), ("Day 4", "Village trail", "Take an easy guided walk through nearby settlement and forest."), ("Day 5", "Return via Talcha", "Transfer to Talcha for the return journey.")],
    },
    "pokhara-kathmandu-tours": {
        "summary": "A culture-and-landscape journey linking Kathmandu's heritage with Pokhara's lakeside calm.",
        "description": "Spend time in Kathmandu's historic squares and living temples, then continue to Pokhara for Phewa Lake, mountain views, and a gentler pace. It is designed for first-time Nepal visitors who want cultural depth without a high-altitude trek.",
        "duration": "5 Days", "duration_days": 5, "price": 560, "difficulty": "easy", "people_count": 14,
        "highlights": ["Kathmandu heritage sites", "Phewa Lake and Pokhara viewpoints", "Private transfers and local guide support"],
        "itinerary": [("Day 1", "Arrive in Kathmandu", "Airport welcome and an evening orientation."), ("Day 2", "Kathmandu heritage day", "Explore key historic squares and temples with a local guide."), ("Day 3", "Drive to Pokhara", "Travel west through river valleys to Pokhara."), ("Day 4", "Pokhara lakeside and viewpoints", "Visit Phewa Lake and a sunrise viewpoint."), ("Day 5", "Return to Kathmandu", "Travel back to Kathmandu for onward departure.")],
    },
    "abc-base-camp-trek": {
        "summary": "An Annapurna Sanctuary trek with extra time for acclimatization and village life.",
        "description": "A fuller Annapurna Base Camp itinerary for travelers who want measured walking days and time to enjoy the changing landscape from foothill villages to the high sanctuary. The route uses trusted local teahouses and a licensed mountain guide.",
        "duration": "9 Days", "duration_days": 9, "price": 780, "difficulty": "moderate", "people_count": 10,
        "highlights": ["Measured acclimatization schedule", "Annapurna Sanctuary sunrise", "Licensed guide and local teahouses"],
        "itinerary": [("Day 1", "Pokhara to Ghandruk", "Transfer to the trail and walk to Ghandruk."), ("Day 2", "Ghandruk to Chhomrong", "Climb to the sanctuary gateway village."), ("Day 3", "Chhomrong to Bamboo", "Forest trail and teahouse stay."), ("Day 4", "Bamboo to Deurali", "Continue through the Modi Khola valley."), ("Day 5", "Deurali to Machhapuchhre Base Camp", "Enter the upper sanctuary beneath Machhapuchhre."), ("Day 6", "Machhapuchhre Base Camp to Annapurna Base Camp", "Short high-altitude walk to the base camp."), ("Day 7", "Annapurna Base Camp to Bamboo", "Return downhill through the sanctuary."), ("Day 8", "Bamboo to Jhinu Danda", "Walk to Jhinu Danda, known for its natural hot springs."), ("Day 9", "Jhinu Danda to Pokhara", "Finish the trek and return to Pokhara.")],
    },
}

GALLERY_IMAGE_TITLES = {
    "annapurna-base-camp-trek": ["Annapurna trekking — Suraz03 (CC BY-SA 3.0)", "Dest Annapurna", "Pkg Annapurna", "Region Annapurna", "Hero Bg"],
    "poon-hill-sunrise-trek": ["Annapurna trekking — Suraz03 (CC BY-SA 3.0)", "Dest Poonhills", "Dl Poonhills", "Region Annapurna", "Seasonal 2"],
    "journey-to-fish-lake": ["Region Rara Lake", "Seasonal 1", "Seasonal 2", "Authentic Nepal", "Hero"],
    "pokhara-kathmandu-tours": ["Experience Pokhara", "Exp Pokhara", "Package Card2", "Region Kathmandu", "Dest Kathmandu"],
    "abc-base-camp-trek": ["Package Card3", "Pkg Annapurna", "Dest Annapurna", "Region Annapurna", "Hero Bg"],
}


class Command(BaseCommand):
    help = "Upsert complete content for Lumora's initial five packages."

    def add_arguments(self, parser):
        parser.add_argument("--download-media", action="store_true", help="Download the Commons Annapurna image into configured Wagtail/Garage storage.")

    def commons_image(self):
        image = CustomImage.objects.filter(title="Annapurna trekking — Suraz03 (CC BY-SA 3.0)").first()
        if image:
            return image
        request = Request(COMMONS_ANNAPURNA, headers={"User-Agent": "LumoraTreks/1.0 media seed"})
        with urlopen(request, timeout=30) as response:
            data = response.read()
        image = CustomImage(title="Annapurna trekking — Suraz03 (CC BY-SA 3.0)", alt_text="Trekkers in Nepal's Annapurna region", caption="Tourists trekking in the Annapurna region", credit="Suraz03 / Wikimedia Commons / CC BY-SA 3.0")
        image.file = ImageFile(BytesIO(data), name="annapurna-trekking-suraz03.jpg")
        image.save()
        return image

    @transaction.atomic
    def handle(self, *args, **options):
        missing = [slug for slug in PACKAGES if not Package.objects.filter(slug=slug).exists()]
        if missing:
            raise CommandError(f"Missing expected package(s): {', '.join(missing)}")
        media = self.commons_image() if options["download_media"] else None
        for slug, data in PACKAGES.items():
            package = Package.objects.get(slug=slug)
            for field in ("summary", "description", "duration", "duration_days", "price", "difficulty", "people_count"):
                setattr(package, field, data[field])
            cover_image = CustomImage.objects.filter(title=GALLERY_IMAGE_TITLES[slug][0]).first()
            if cover_image:
                package.image = cover_image
            elif media:
                package.image = media
            package.save()
            package.highlights.all().delete(); package.itinerary.all().delete(); package.included_items.all().delete(); package.gallery.all().delete()
            for order, text in enumerate(data["highlights"], 1): PackageHighlight.objects.create(package=package, text=text, sort_order=order)
            for order, (label, title, description) in enumerate(data["itinerary"], 1): PackageItineraryDay.objects.create(package=package, day_label=label, title=title, description=description, sort_order=order)
            for order, text in enumerate(["Licensed local guide", "Teahouse accommodation", "Daily breakfast", "Required permits", "Ground transfers"], 1): PackageIncludedItem.objects.create(package=package, kind="included", text=text, sort_order=order)
            for order, text in enumerate(["International flights", "Travel insurance", "Personal expenses", "Meals not listed"], 1): PackageIncludedItem.objects.create(package=package, kind="excluded", text=text, sort_order=order)
            for order, image_title in enumerate(GALLERY_IMAGE_TITLES[slug], 1):
                image = CustomImage.objects.filter(title=image_title).first()
                if image:
                    PackageGalleryImage.objects.create(package=package, image=image, caption=f"{package.title} — photo {order}", sort_order=order)
            self.stdout.write(f"Updated {package.title}")
