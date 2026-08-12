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

from apps.catalog.models import Destination, Package, Testimonial
from apps.cms.models import HomePage
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
        home = self.create_home_page()
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
                    "heading": "Discover the soul of Nepal with major hospitality of Lumora Treks",
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
                        card("Dhorpatan Region"),
                        card("Patan"),
                        card("Pokhara"),
                    ],
                    "feature_card": card(
                        "Rara Lake",
                        variant="big-package",
                        layout="large",
                        description=(
                            "Escape into Nepal's only hunting reserve, where rolling alpine "
                            "meadows, peaceful villages, and panoramic mountain views create the "
                            "perfect off-the-beaten-path adventure."
                        ),
                        image_stem="destination-card-default",
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
                        "eyebrow": "Curated Travel Experiences",
                        "heading": "Explore the Heart of Nepal",
                        "description": (
                            "From ancient temples to towering peaks, discover the regions that make "
                            "Nepal an unforgettable destination."
                        ),
                        "align": "center",
                    },
                    "variant": "welcome",
                    "source": "selected",
                    "items": [
                        card("Annapurna Region", variant="big-package", layout="large"),
                        card("Bandipur"),
                        card("Kathmandu"),
                        card("Swayambhunath"),
                        card("Rara Lake"),
                        card("Everest Region"),
                    ],
                    "limit": 6,
                    "settings": self.settings("regions"),
                },
            },
            {
                "type": "features_list",
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
                    "image": self.pk("features-decorative"),
                    "image_position": "left",
                    "items": [
                        {
                            "number": "01",
                            "title": "Authentic Experiences",
                            "description": (
                                "Go beyond tourist attractions and immerse yourself in local "
                                "cultures, traditions, and hidden gems."
                            ),
                            "icon": "",
                        },
                        {
                            "number": "02",
                            "title": "Hassle-Free Planning",
                            "description": (
                                "From accommodations to transportation, we handle every detail so "
                                "you can focus on making memories."
                            ),
                            "icon": "",
                        },
                        {
                            "number": "03",
                            "title": "Safe & Reliable Travel",
                            "description": (
                                "Enjoy peace of mind with verified travel partners, expert guidance, "
                                "and dedicated support throughout your journey."
                            ),
                            "icon": "",
                        },
                    ],
                    "settings": self.settings("features"),
                },
            },
            {
                "type": "testimonial",
                "value": {
                    "background_image": self.pk("testimonial-bg"),
                    "background_video": None,
                    "overlay_opacity": 70,
                    "testimonial": testimonial.pk if testimonial else None,
                    "quote": "",
                    "quote_highlights": ["Lumora Treks", "made just for us"],
                    "author_name": "",
                    "author_role": "",
                    "show_quote_icon": True,
                    "settings": self.settings("testimonial", container="default"),
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
                "type": "stats_banner",
                "value": {
                    "background_image": self.pk("stats-bg"),
                    "background_video": None,
                    "overlay_opacity": 75,
                    "heading": "",
                    "stats": [
                        {"value": "24%", "label": "Repeated Business", "icon": ""},
                        {"value": "180K", "label": "Guest satisfied", "icon": ""},
                        {"value": "10+", "label": "Month of Working", "icon": ""},
                    ],
                    "settings": self.settings("stats"),
                },
            },
            {
                "type": "bento_grid",
                "value": {
                    "heading": {
                        "eyebrow": "Most Visit Destinations in Nepal",
                        "heading": "Seasonal Special Destinations",
                        "description": (
                            "Handpicked getaways that shine brightest depending on the season you "
                            "choose to travel."
                        ),
                        "align": "center",
                    },
                    "variant": "seasonal",
                    "source": "selected",
                    "items": [
                        card("Journey to Fish Lake", variant="package-card", layout="tall"),
                        card("Gosaikunda Trail", variant="package-card", layout="tall"),
                        card("Chitwan Safari", variant="package-card", layout="wide"),
                        card("Mustang Valley", variant="package-card", layout="small"),
                        card("Langtang Valley", variant="package-card", layout="small"),
                    ],
                    "limit": 5,
                    "settings": self.settings("destinations"),
                },
            },
        ]

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
                {"type": "item", "value": self.nav_item("Packages", "anchor", anchor="packages")},
                {"type": "item", "value": self.nav_item("Destinations", "anchor", anchor="destinations")},
                {"type": "item", "value": self.nav_item("Contact Us", "anchor", anchor="contact")},
            ]
            nav.cta_button = [
                {
                    "type": "button",
                    "value": {
                        **self.empty_button(),
                        "label": "Reserve Now",
                        "link_type": "anchor",
                        "anchor": "contact",
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
                "Discover expertly crafted itineraries, local experiences, and seamless bookings "
                "that turn every journey into a story worth telling."
            )
            footer.columns = [
                {
                    "type": "column",
                    "value": {
                        "heading": "Explore",
                        "links": [
                            self.link("Home", "url", url="/"),
                            self.link("Packages", "anchor", anchor="packages"),
                            self.link("Destinations", "anchor", anchor="destinations"),
                            self.link("About Us", "url", url="/about"),
                        ],
                    },
                },
                {
                    "type": "column",
                    "value": {
                        "heading": "Support",
                        "links": [
                            self.link("Contact Us", "anchor", anchor="contact"),
                            self.link("FAQs", "anchor", anchor="faq"),
                            self.link("Privacy Policy", "url", url="/privacy"),
                            self.link("Terms of Service", "url", url="/terms"),
                        ],
                    },
                },
            ]
            footer.socials = [
                {"type": "social", "value": {"platform": "Facebook", "icon": "mdi:facebook", "url": "https://facebook.com"}},
                {"type": "social", "value": {"platform": "Instagram", "icon": "mdi:instagram", "url": "https://instagram.com"}},
                {"type": "social", "value": {"platform": "Twitter", "icon": "mdi:twitter", "url": "https://twitter.com"}},
                {"type": "social", "value": {"platform": "YouTube", "icon": "mdi:youtube", "url": "https://youtube.com"}},
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
