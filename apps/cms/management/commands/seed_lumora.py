"""
Seed the CMS with the current frontend homepage.

Imports the images from `lumora-treks-FE/public/images`, creates the package /
destination / testimonial library, fills in the site settings, and builds a
Home page whose blocks reproduce `src/app/page.tsx` section for section — so
the frontend can switch from hardcoded data to the API with no visual change.

    python manage.py seed_lumora            # create (skips existing objects)
    python manage.py seed_lumora --reset    # rebuild the home page body
"""

from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page, Site

from apps.catalog.models import (
    Destination,
    Package,
    PackageHighlight,
    PackageIncludedItem,
    PackageItineraryDay,
    PackageRatingSummary,
    Testimonial,
)
from apps.cms.models import HomePage, PackageIndexPage, StandardPage
from apps.core.models import CustomImage
from apps.navigation.models import (
    BrandSettings,
    FooterSettings,
    IntegrationSettings,
    NavigationSettings,
    ThemeSettings,
)

FE_IMAGE_DIR = Path(__file__).resolve().parents[5] / "lumora-treks-FE" / "public" / "images"


class Command(BaseCommand):
    help = "Populate the CMS with the Lumora Treks home page, media and settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite the home page body and site settings with the seed content.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.reset = options["reset"]
        self.images = {}

        self.import_images()
        self.create_destinations()
        self.create_packages()
        self.create_testimonials()
        self.create_package_details()
        home = self.create_home_page()
        self.create_editorial_pages(home)
        self.create_settings()

        self.stdout.write(self.style.SUCCESS(f"Seeded home page: {home.title} (id={home.pk})"))
        self.stdout.write("Admin:    http://localhost:8000/admin/")
        self.stdout.write("Home API: http://localhost:8000/api/v2/page-by-path/?path=/")

    # ------------------------------------------------------------------ media

    def import_images(self):
        if not FE_IMAGE_DIR.exists():
            self.stdout.write(
                self.style.WARNING(f"Frontend images not found at {FE_IMAGE_DIR} — skipping import.")
            )
            return

        for path in sorted(FE_IMAGE_DIR.glob("*.png")):
            title = path.stem.replace("-", " ").title()
            existing = CustomImage.objects.filter(title=title).first()
            if existing:
                self.images[path.stem] = existing
                continue
            with path.open("rb") as handle:
                image = CustomImage(title=title, alt_text=title)
                image.file = ImageFile(handle, name=path.name)
                image.save()
            self.images[path.stem] = image
        self.stdout.write(f"Images available: {len(self.images)}")

    def image(self, stem):
        return self.images.get(stem)

    # --------------------------------------------------------------- catalog

    def create_destinations(self):
        regions = [
            ("Annapurna Region", "region-annapurna", "large", True),
            ("Bandipur", "region-bandipur", "small", True),
            ("Kathmandu", "region-kathmandu", "small", True),
            ("Swayambhunath", "region-swayambhunath", "small", True),
            ("Rara Lake", "region-rara-lake", "small", True),
            ("Everest Region", "region-everest", "small", True),
            ("Dhorpatan Region", "experience-dhorpatan", "small", False),
            ("Patan", "experience-patan", "small", False),
            ("Pokhara", "experience-pokhara", "small", False),
        ]
        for order, (title, image_stem, layout, featured) in enumerate(regions):
            Destination.objects.get_or_create(
                title=title,
                defaults={
                    "image": self.image(image_stem),
                    "default_layout": layout,
                    "is_featured": featured,
                    "sort_order": order,
                    "region": title.replace(" Region", ""),
                },
            )

        # Preserve the complete destination catalogue that existed in the old
        # frontend.  These are deliberately explicit slugs so repeated seed
        # runs are idempotent and the old links keep resolving.
        legacy_destinations = [
            ("Poon Hills", "poon-hills", "dl-poonhills", "large", "Annapurna", True),
            ("Chandragiri Hills", "chandragiri-hills", "dl-chandragiri", "small", "Kathmandu", True),
            ("Kathmandu Valley", "kathmandu-valley", "dl-kathmandu", "large", "Kathmandu", True),
            ("Swayubhunath", "swayubhunath", "region-swayambhunath", "small", "Kathmandu", True),
            ("Annapurna Base Camp", "annapurna-base-camp", "dest-annapurna", "small", "Annapurna", True),
            ("Chitwan", "chitwan", "dest-chitwan", "small", "Chitwan", True),
        ]
        for order, (title, slug, image_stem, layout, region, featured) in enumerate(
            legacy_destinations, start=len(regions)
        ):
            Destination.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "image": self.image(image_stem),
                    "default_layout": layout,
                    "is_featured": featured,
                    "sort_order": order,
                    "region": region,
                },
            )

        seasonal = [
            ("Journey to Fish Lake", "seasonal-1", "tall"),
            ("Gosaikunda Trail", "seasonal-2", "tall"),
            ("Chitwan Safari", "seasonal-3", "wide"),
            ("Mustang Valley", "seasonal-4", "tall"),
            ("Langtang Valley", "seasonal-5", "tall"),
        ]
        for order, (title, image_stem, layout) in enumerate(seasonal, start=len(regions)):
            Destination.objects.get_or_create(
                title=title,
                defaults={
                    "image": self.image(image_stem),
                    "default_layout": layout,
                    "best_season": "Autumn",
                    "sort_order": order,
                },
            )

        # The old gallery used five cards with the same display title. Keep
        # each card as its own CMS destination (rather than collapsing them
        # into one record) so its image and bento layout survive the migration.
        for order, (image_stem, layout) in enumerate(
            [("seasonal-1", "tall"), ("seasonal-2", "tall"), ("seasonal-3", "wide"),
             ("seasonal-4", "tall"), ("seasonal-5", "tall")],
            start=len(regions) + len(legacy_destinations) + len(seasonal),
        ):
            Destination.objects.get_or_create(
                slug=image_stem,
                defaults={
                    "title": "Journey to fish lake",
                    "image": self.image(image_stem),
                    "default_layout": layout,
                    "best_season": "Autumn",
                    "sort_order": order,
                },
            )

    def create_packages(self):
        packages = [
            ("Journey to fish lake", "package-card1", 400.23),
            ("Pokhara & Kathmandu Tours", "package-card2", 400.23),
            ("ABC Base Camp Trek", "package-card3", 400.23),
        ]
        for order, (title, image_stem, price) in enumerate(packages):
            Package.objects.get_or_create(
                title=title,
                defaults={
                    "image": self.image(image_stem),
                    "summary": "A handpicked Nepal experience crafted by local guides.",
                    "rating": 4.5,
                    "duration": "4 days & 3 nights",
                    "duration_days": 4,
                    "people_count": 30,
                    "price": price,
                    "currency": "USD",
                    "difficulty": "moderate",
                    "is_popular": True,
                    "sort_order": order,
                    "includes": "Airport transfers\nLicensed guide\nAccommodation\nBreakfast",
                    "excludes": "International flights\nTravel insurance\nPersonal expenses",
                },
            )

        # Legacy FE catalogue: three popular cards, fifteen filtered cards and
        # the three cultural-tour cards.  Preserve every card/image as a real
        # package so the current FE never needs a static fallback.
        legacy = [
            ("dhorpatan-region", "Dhorpatan Region", "pkg-dhorpatan", "Trekking", True),
            ("pokhara-tours", "Pokhara Tours", "pkg-pokhara", "Sightseeing", True),
            ("ghandruk-annapurna", "Ghandruk and Annapurna region", "pkg-annapurna", "Trekking", True),
        ]
        titles = ["Dhorpatan Region", "Pokhara Tours", "Ghandruk and Annapurna region"]
        for category, prefix, count in (("Trekking", "trek", 8), ("Sightseeing", "sight", 4), ("Paragliding", "para", 3)):
            for index in range(count):
                legacy.append((
                    f"{prefix}-{index + 1}",
                    titles[index % len(titles)],
                    f"pkgp-{(index % 6) + 1}",
                    category,
                    False,
                ))
        legacy.extend([
            ("cultural-dhorpatan", "Dhorpatan Region", "cultural-1", "Sightseeing", False),
            ("cultural-pokhara", "Pokhara Tours", "cultural-2", "Sightseeing", False),
            ("cultural-ghandruk", "Ghandruk and Annapurna region", "pkgp-3", "Sightseeing", False),
        ])
        for order, (slug, title, image_stem, category, popular) in enumerate(legacy, start=len(packages)):
            Package.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": category,
                    "summary": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor .",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor .",
                    "image": self.image(image_stem),
                    "rating": 4.9,
                    "duration": "4 Days",
                    "duration_days": 4,
                    "people_count": 1,
                    "price": 400,
                    "currency": "USD",
                    "is_popular": popular,
                    "sort_order": order,
                    "includes": "",
                    "excludes": "",
                },
            )

    def create_testimonials(self):
        Testimonial.objects.get_or_create(
            author_name="Sarah Whitman",
            defaults={
                "author_role": "Everest Base Camp Trekker",
                "quote": (
                    "Traveling with Lumora Treks was the best decision we made this year — "
                    "every trail, every sunrise, and every local story felt like it was "
                    "made just for us."
                ),
                "rating": 5,
                "is_featured": True,
            },
        )

    def create_package_details(self):
        """Populate reusable itinerary/highlight/review rows for every package.

        Package.rating and Package.review_count are maintained as denormalized
        aggregates so catalogue/list requests do not need COUNT/AVG joins.
        The underlying Testimonial rows remain available for detail pages and
        future real review submissions.
        """
        review_templates = [
            ("Maya Sharma", "Verified traveller", "A smooth, thoughtful Nepal journey with excellent local guidance.", 5),
            ("Daniel Carter", "Adventure traveller", "Beautiful routes, clear planning, and memorable experiences from start to finish.", 5),
        ]
        itinerary_titles = [
            "Arrival and local orientation",
            "Scenic transfer and guided exploration",
            "Signature experience and free time",
            "Departure and onward travel",
        ]
        for package in Package.objects.all():
            for order, title in enumerate(itinerary_titles, start=1):
                day_label = f"Day {order}"
                day = PackageItineraryDay.objects.filter(package=package, day_label=day_label).first()
                if day is None:
                    day = PackageItineraryDay(package=package, day_label=day_label)
                day.title = f"{title} — {package.title}"
                day.description = (
                    "A carefully paced day with local support, practical transfers, and time "
                    "to experience Nepal beyond the itinerary."
                )
                day.sort_order = order
                day.save()

            for order, text in enumerate(
                ["Local guide support", "Curated transfers", "Authentic local experiences"], start=1
            ):
                highlight = PackageHighlight.objects.filter(package=package, text=text).first()
                if highlight is None:
                    highlight = PackageHighlight(package=package, text=text)
                highlight.sort_order = order
                highlight.save()

            normalized_items = [
                ("included", "Airport transfers"),
                ("included", "Licensed local guide"),
                ("included", "Accommodation and breakfast"),
                ("excluded", "International flights"),
                ("excluded", "Travel insurance"),
                ("excluded", "Personal expenses"),
            ]
            for order, (kind, text) in enumerate(normalized_items, start=1):
                item, _ = PackageIncludedItem.objects.get_or_create(
                    package=package, kind=kind, text=text
                )
                item.sort_order = order
                item.save(update_fields=["sort_order"])

            for order, (author, role, quote, rating) in enumerate(review_templates, start=1):
                review, created = Testimonial.objects.get_or_create(
                    author_name=author,
                    package=package,
                    defaults={
                        "author_role": role,
                        "quote": quote,
                        "rating": rating,
                        "sort_order": order,
                    },
                )
                if not created:
                    review.author_role = role
                    review.quote = quote
                    review.rating = rating
                    review.sort_order = order
                    review.save(update_fields=["author_role", "quote", "rating", "sort_order"])

            reviews = Testimonial.objects.filter(package=package)
            count = reviews.count()
            if count:
                average = sum(review.rating for review in reviews) / count
                package.review_count = count
                package.rating = round(average, 1)
                package.save(update_fields=["review_count", "rating"])
            else:
                average = 0

            ratings = [review.rating for review in reviews]
            summary, _ = PackageRatingSummary.objects.get_or_create(package=package)
            summary.total_reviews = count
            summary.rating_sum = sum(ratings)
            summary.average_rating = round(average, 1)
            summary.one_star = ratings.count(1)
            summary.two_star = ratings.count(2)
            summary.three_star = ratings.count(3)
            summary.four_star = ratings.count(4)
            summary.five_star = ratings.count(5)
            summary.save()

    # ------------------------------------------------------------------ page

    def create_home_page(self):
        home = HomePage.objects.first()
        if home and not self.reset:
            self.stdout.write("Home page already exists — pass --reset to rebuild its body.")
            return home

        if home is None:
            root = Page.objects.get(depth=1)
            # Remove the placeholder page Wagtail creates on a fresh install.
            for placeholder in root.get_children().filter(slug="home").exclude(id__in=[]):
                if placeholder.specific_class is Page:
                    placeholder.delete()

            home = HomePage(
                title="Home",
                slug="home",
                seo_title="Lumora Treks | Travel Beyond Destinations",
                search_description=(
                    "Discover expertly crafted itineraries, local experiences, and seamless "
                    "bookings that turn every journey into a story worth telling."
                ),
            )
            root.add_child(instance=home)

            site = Site.objects.filter(is_default_site=True).first()
            if site:
                site.root_page = home
                site.site_name = "Lumora Treks"
                site.save()
            else:
                Site.objects.create(
                    hostname="localhost", port=80, root_page=home, is_default_site=True, site_name="Lumora Treks"
                )

        home.body = self.build_home_body()
        home.save_revision().publish()
        return home

    def build_home_body(self):
        """One entry per section in `src/app/page.tsx`, in the same order."""
        destinations = {d.title: d for d in Destination.objects.all()}
        testimonial = Testimonial.objects.filter(author_name="Sarah Whitman").first()

        def card(title, variant="default", layout="small", description="", image_stem=None):
            destination = destinations.get(title)
            return {
                "destination": destination.pk if destination else None,
                "title": "" if destination else title,
                "description": description,
                "image": self.image(image_stem).pk if image_stem and self.image(image_stem) else None,
                "variant": variant,
                "layout": layout,
                "link": self.empty_link(),
                }

        return [
            {
                "type": "hero",
                "value": {
                    "heading": "Travel beyond destinations",
                    "slides": [
                        {"image": self.pk("hero"), "alt": "Nepal mountain landscape"},
                        {"image": self.pk("region-everest"), "alt": "Everest region peaks"},
                        {"image": self.pk("region-annapurna"), "alt": "Annapurna region trail"},
                    ],
                    "mountain_cutout": True,
                    "show_search": True,
                    "search_location_label": "Location",
                    "search_location_placeholder": "Where to go?",
                    "search_date_label": "Date",
                    "search_date_placeholder": "Add dates",
                    "search_button_label": "Search",
                    "buttons": [],
                    "settings": self.settings("hero", background="default", container="full"),
                },
            },
            {
                "type": "intro_stats",
                "value": {
                    "heading": (
                        "We've helped thousands of travelers discover unforgettable journeys "
                        "across the world"
                    ),
                    "highlight": "unforgettable journeys",
                    "description": (
                        "From iconic landmarks to hidden gems, we curate authentic travel "
                        "experiences that inspire exploration, create lasting memories, and make "
                        "every journey seamless from start to finish."
                    ),
                    "description_highlight": "and make every journey seamless from start to finish.",
                    "stats": [
                        {"value": "24K+", "label": "Happy Travelers", "icon": ""},
                        {"value": "120", "label": "Cured Destinations", "icon": ""},
                        {"value": "4.9", "label": "Overall Ratings", "icon": ""},
                    ],
                    "settings": self.settings("about", container="narrow"),
                },
            },
            {
                "type": "popular_packages",
                "value": {
                    "heading": {
                        "eyebrow": "Handpicked For You",
                        "heading": "Popular Packages",
                        "description": (
                            "Explore our most loved travel packages, crafted for adventurers who "
                            "want more than just a trip."
                        ),
                        "align": "center",
                    },
                    "source": "popular",
                    "packages": [],
                    "destination": None,
                    "sdk_package_ids": [],
                    "limit": 8,
                    "autoplay": False,
                    "show_price": True,
                    "cta": self.empty_button(),
                    "settings": self.settings("packages"),
                },
            },
            {
                "type": "experience_showcase",
                "value": {
                    "heading": "Discover the soul of Nepal with with major hospitality of Lumora Treks",
                    "description": (
                        "From the snow-capped Himalayas to ancient heritage cities and lush "
                        "wildlife reserves, every destination is carefully selected to offer "
                        "authentic experiences, breathtaking scenery, and unforgettable memories."
                    ),
                    "description_highlight": (
                        "offer authentic experiences, breathtaking scenery, and unforgettable memories."
                    ),
                    "show_arrows": True,
                    "small_cards": [
                        card("Dhorpatan Region", image_stem="exp-dhorpatan"),
                        card("Patan", image_stem="exp-patan"),
                        card("Pokhara", image_stem="exp-pokhara"),
                    ],
                    "feature_card": card(
                        "Dhorpatan Region",
                        variant="big-package",
                        layout="large",
                        description=(
                            "Escape into Nepal's only hunting reserve, where rolling alpine "
                            "meadows, peaceful villages, and panoramic mountain views create the "
                            "perfect off-the-beaten-path adventure."
                        ),
                        image_stem="exp-big",
                    ),
                    "settings": self.settings("experience"),
                },
            },
            {
                "type": "why_choose_us",
                "value": {
                    "heading": {
                        "eyebrow": "",
                        "heading": "Why Lumora Treks?",
                        "description": (
                            "We make every journey effortless, memorable, and uniquely yours. From "
                            "carefully curated destinations to trusted local expertise, we're "
                            "committed to delivering travel experiences that go beyond expectations."
                        ),
                        "align": "center",
                    },
                    "description_highlight": (
                        "we're committed to delivering travel experiences that go beyond expectations."
                    ),
                    "cards": [
                        {
                            "theme": "light",
                            "heading": "Curated Destinations",
                            "description": (
                                "Every destination is handpicked to showcase the best of nature, "
                                "culture, and adventure, ensuring every trip is truly unforgettable."
                            ),
                            "image": self.pk("why-circle-1"),
                            "link": self.empty_link(),
                        },
                        {
                            "theme": "dark",
                            "heading": "Seamless Travel Planning",
                            "description": (
                                "From personalized itineraries and accommodations to transportation "
                                "and local experiences, we handle every detail so you can simply "
                                "enjoy the journey."
                            ),
                            "image": self.pk("why-circle-2"),
                            "link": self.empty_link(),
                        },
                        {
                            "theme": "light",
                            "heading": "Trusted Local Expertise",
                            "description": (
                                "Travel with confidence through experienced local guides, reliable "
                                "partners, and insider recommendations that help you discover "
                                "destinations like never before."
                            ),
                            "image": self.pk("why-circle-3"),
                            "link": self.empty_link(),
                        },
                    ],
                    "settings": self.settings("why-us"),
                },
            },
            {
                "type": "bento_grid",
                "value": {
                    "heading": {
                        "eyebrow": "",
                        "heading": "Explore famous destinations",
                        "description": "Whether you're seeking mountain adventures, wildlife encounters.",
                        "align": "left",
                    },
                    "variant": "welcome",
                    "source": "selected",
                    "items": [
                        card("Dhorpatan Region", image_stem="dest-dhorpatan"),
                        card("Poon Hills", image_stem="dest-poonhills", variant="big-package", layout="large"),
                        card("Annapurna Base Camp", image_stem="dest-annapurna"),
                        card("Chitwan", image_stem="dest-chitwan"),
                        card("Kathmandu Valley", image_stem="dest-kathmandu"),
                    ],
                    "limit": 6,
                    "settings": self.settings("regions"),
                },
            },
            {
                "type": "authentic_experiences",
                "value": {
                    "heading": "Discover Nepal Through Authentic Experiences with Us",
                    "description": (
                        "From the majestic Himalayas and ancient heritage sites to serene lakes and "
                        "vibrant local cultures, Lumora Treks helps you experience Nepal beyond the "
                        "ordinary."
                    ),
                    "description_highlight": (
                        "Lumora Treks helps you experience Nepal beyond the ordinary."
                    ),
                    "image": self.pk("authentic-nepal"),
                    "reversed": False,
                    "items": [
                        {
                            "number": "01",
                            "title": "Authentic Experiences",
                            "description": (
                                "Go beyond tourist attractions and immerse yourself in local "
                                "cultures, traditions, and hidden gems."
                            ),
                        },
                        {
                            "number": "02",
                            "title": "Hassle-Free Planning",
                            "description": (
                                "From accommodations to transportation, we handle every detail so "
                                "you can focus on making memories."
                            ),
                        },
                        {
                            "number": "03",
                            "title": "Safe & Reliable Travel",
                            "description": (
                                "Enjoy peace of mind with verified travel partners, expert guidance, "
                                "and dedicated support throughout your journey."
                            ),
                        },
                    ],
                    "settings": self.settings("features"),
                },
            },
            {
                "type": "faq",
                "value": {
                    "heading": {
                        "eyebrow": "",
                        "heading": "Frequently Asked Questions",
                        "description": "These are the questions we hear more often.",
                        "align": "center",
                    },
                    "items": [
                        {
                            "question": "Is this secure?",
                            "answer": (
                                "<p>Every destination is handpicked to showcase the best of nature, "
                                "culture, and adventure, ensuring every trip is truly unforgettable.</p>"
                            ),
                            "open_by_default": True,
                        },
                        {"question": "How can we reach out to you?", "answer": "", "open_by_default": False},
                        {"question": "Address of your place", "answer": "", "open_by_default": False},
                        {"question": "How to contact with agency?", "answer": "", "open_by_default": False},
                        {
                            "question": "How to book appointment to your place?",
                            "answer": "",
                            "open_by_default": False,
                        },
                    ],
                    "show_side_card": True,
                    "side_card_heading": "Don't see the answer you need?",
                    "side_card_text": (
                        "That's ok. Just drop a message and we will get back to you ASAP."
                    ),
                    "side_card_button": {
                        **self.empty_button(),
                        "label": "Contact Us",
                        "link_type": "anchor",
                        "anchor": "contact",
                        "style": "secondary",
                        "size": "md",
                    },
                    "settings": self.settings("faq"),
                },
            },
            {
                "type": "cta_banner",
                "value": {
                    "heading": "Create memories that stay with you long after the Journey Ends",
                    "text": "",
                    "background_image": self.pk("cta-bg"),
                    "buttons": [{
                        **self.empty_button(),
                        "label": "Reserve Now",
                        "link_type": "url",
                        "url": "/enquiry",
                    }],
                    "settings": self.settings("contact", container="full"),
                },
            },
        ]

    def create_editorial_pages(self, home):
        """Create the initial public page tree with page-owned StreamField data.

        These blocks are deliberately attached to their *page*, never to a
        reusable component definition. Editors can therefore reorder, remove,
        and configure a section without changing any other page.
        """

        def upsert(page_class, title, slug, body, **fields):
            page = home.get_children().type(page_class).filter(slug=slug).first()
            if page:
                page = page.specific
            else:
                page = page_class(title=title, slug=slug, **fields)
                home.add_child(instance=page)
            if self.reset or not page.body:
                page.body = body
                for field, value in fields.items():
                    setattr(page, field, value)
                page.save_revision().publish()
            return page

        upsert(
            PackageIndexPage,
            "Packages",
            "packages",
            [
                {
                    "type": "page_hero",
                    "value": {
                        "title": "Discover your next adventure",
                        "subtitle": "Choose from carefully crafted journeys across Nepal.",
                        "image": self.pk("packages-hero"),
                        "image_alt": "Nepal travel experiences",
                        "image_width": 565,
                        "image_height": 457,
                        "show_search": True,
                        "settings": self.settings("hero"),
                    },
                },
                {
                    "type": "package_listing",
                    "value": {
                        "heading": "Popular Packages",
                        "categories": ["Trekking", "Sightseeing", "Paragliding"],
                        "page_size": 6,
                        "default_category": "Trekking",
                        "show_filters": True,
                        "settings": self.settings("packages"),
                    },
                },
                {
                    "type": "cultural_tours",
                    "value": {
                        "heading": "Cultural & Day Tours",
                        "description": "Discover Nepal's heritage, food, and local stories.",
                        "source": "selected",
                        "packages": list(Package.objects.filter(slug__startswith="cultural-").values_list("pk", flat=True)),
                        "destination": None,
                        "sdk_package_ids": [],
                        "limit": 6,
                        "autoplay": False,
                        "show_price": True,
                        "cta": self.empty_button(),
                        "settings": self.settings("cultural-tours"),
                    },
                },
            ],
            intro="Browse trips by style, destination, and travel pace.",
            packages_per_page=6,
            show_filters=True,
        )

        upsert(
            StandardPage,
            "Destinations",
            "destinations",
            [
                {
                    "type": "page_hero",
                    "value": {
                        "title": "Explore Nepal's remarkable destinations",
                        "subtitle": "From high Himalayan trails to living heritage cities.",
                        "image": self.pk("destinations-hero"),
                        "image_alt": "Nepal destinations",
                        "image_width": 565,
                        "image_height": 457,
                        "show_search": True,
                        "settings": self.settings("hero"),
                    },
                },
                {
                    "type": "destinations_grid",
                    "value": {
                        "heading": "Our Destinations",
                        "source": "featured",
                        "destinations": [],
                        "limit": 12,
                        "settings": self.settings("destinations"),
                    },
                },
            ],
            intro="Explore the places that make Nepal unforgettable.",
        )

        upsert(
            StandardPage,
            "Contact Us",
            "contact",
            [
                {
                    "type": "page_hero",
                    "value": {
                        "title": "Create memories beyond maps",
                        "subtitle": "Tell us how you want to travel and our local team will help shape the journey.",
                        "image": self.pk("packages-hero"),
                        "image_alt": "Nepal landscapes",
                        "image_width": 565,
                        "image_height": 457,
                        "show_search": False,
                        "settings": self.settings("contact-hero"),
                    },
                },
                {
                    "type": "lead_form",
                    "value": {
                        "heading": {"eyebrow": "", "heading": "Leave your message", "description": "We reply within one business day.", "align": "left"},
                        "form_key": "contact",
                        "fields": [
                            {"name": "name", "label": "Name", "field_type": "text", "placeholder": "Your name", "required": True, "options": [], "width": "half"},
                            {"name": "email", "label": "Email address", "field_type": "email", "placeholder": "you@example.com", "required": True, "options": [], "width": "half"},
                            {"name": "destination", "label": "Destination", "field_type": "text", "placeholder": "Where would you like to go?", "required": False, "options": [], "width": "full"},
                            {"name": "message", "label": "Message", "field_type": "textarea", "placeholder": "Tell us about your trip", "required": True, "options": [], "width": "full"},
                        ],
                        "submit_label": "Send message",
                        "success_message": "Thanks — we'll get back to you within one business day.",
                        "notification_email": "",
                        "image": None,
                        "settings": self.settings("contact-form"),
                    },
                },
            ],
            intro="Get in touch with Lumora Treks.",
        )

        upsert(
            StandardPage,
            "Privacy Policy",
            "privacy",
            [
                {
                    "type": "rich_text",
                    "value": {
                        "heading": "Privacy Policy",
                        "body": "<h2>Information we collect</h2><p>We collect the information you provide when you contact us, request a trip, or make a booking.</p><h2>How we use your information</h2><p>We use it to respond to enquiries, arrange travel, provide support, and meet legal obligations.</p><h2>Your choices</h2><p>You may request access to, correction of, or deletion of your personal information, subject to applicable obligations.</p>",
                        "width": "narrow",
                        "settings": self.settings("privacy"),
                    },
                }
            ],
            intro="How Lumora Treks handles your personal information.",
        )

    # ------------------------------------------------------------- helpers

    def pk(self, stem):
        image = self.image(stem)
        return image.pk if image else None

    @staticmethod
    def settings(anchor_id="", background="default", spacing="md", container="default"):
        return {
            "anchor_id": anchor_id,
            "background": background,
            "spacing": spacing,
            "container": container,
            "hidden": False,
        }

    @staticmethod
    def empty_link():
        return {
            "label": "",
            "link_type": "url",
            "page": None,
            "url": "",
            "anchor": "",
            "document": None,
            "email": "",
            "phone": "",
            "open_in_new_tab": False,
        }

    @classmethod
    def empty_button(cls):
        return {**cls.empty_link(), "style": "primary", "size": "md", "icon": ""}

    # ------------------------------------------------------------ settings

    def create_settings(self):
        brand, created = BrandSettings.objects.get_or_create(pk=1)
        if created or self.reset:
            brand.site_name = "Lumora Treks"
            brand.tagline = "Travel beyond destinations"
            brand.logo_icon = "ph:mountains-fill"
            brand.default_meta_title = "Lumora Treks | Travel Beyond Destinations"
            brand.default_meta_description = (
                "Discover expertly crafted itineraries, local experiences, and seamless bookings "
                "that turn every journey into a story worth telling."
            )
            brand.email = "hello@lumoratreks.com"
            brand.phone = "+977 1 4000000"
            brand.address = "Thamel, Kathmandu, Nepal"
            brand.save()

        nav, created = NavigationSettings.objects.get_or_create(pk=1)
        if created or self.reset:
            nav.items = [
                {"type": "item", "value": self.nav_item("Home", "url", url="/")},
                {"type": "item", "value": self.nav_item("Packages", "url", url="/packages")},
                {"type": "item", "value": self.nav_item("Destinations", "url", url="/destinations")},
                {"type": "item", "value": self.nav_item("Contact Us", "url", url="/contact")},
            ]

            nav.cta_button = [
                {
                    "type": "button",
                    "value": {
                        **self.empty_button(),
                        "label": "Reserve Now",
                        "link_type": "url",
                        "url": "/enquiry",
                        "style": "secondary",
                        "size": "sm",
                    },
                }
            ]
            nav.sticky = True
            nav.save()

        footer, created = FooterSettings.objects.get_or_create(pk=1)
        if created or self.reset:
            footer.description = (
                "Your trusted travel partner in Nepal. We curate authentic experiences, "
                "breathtaking destinations, and unforgettable memories."
            )
            footer.columns = [
                {
                    "type": "column",
                    "value": {
                        "heading": "",
                        "links": [
                            self.link("Contact Us", "url", url="/contact"),
                            self.link("Privacy Policy", "url", url="/privacy"),
                            self.link("Terms & Conditions", "url", url="/terms"),
                            self.link("Login to Admin Portal", "url", url="/admin"),
                        ],
                    },
                },
            ]
            footer.socials = [
                {"type": "social", "value": {"platform": "Facebook", "icon": "mdi:facebook", "url": "#"}},
                {"type": "social", "value": {"platform": "Instagram", "icon": "mdi:instagram", "url": "#"}},
                {"type": "social", "value": {"platform": "X", "icon": "prime:twitter", "url": "#"}},
                {"type": "social", "value": {"platform": "WhatsApp", "icon": "mdi:whatsapp", "url": "#"}},
            ]
            footer.newsletter_enabled = True
            footer.newsletter_heading = "Newsletter"
            footer.newsletter_text = "Subscribe to get the latest travel deals and stories."
            footer.secondary_text = "Designed & built with care for travelers everywhere."
            footer.save()

        ThemeSettings.objects.get_or_create(pk=1)
        IntegrationSettings.objects.get_or_create(pk=1)

    @classmethod
    def link(cls, label, link_type, url="", anchor=""):
        return {**cls.empty_link(), "label": label, "link_type": link_type, "url": url, "anchor": anchor}

    @classmethod
    def nav_item(cls, label, link_type, url="", anchor=""):
        return {
            **cls.link(label, link_type, url=url, anchor=anchor),
            "icon": "",
            "children": [],
            "highlight": False,
        }
