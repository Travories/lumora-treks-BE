"""
The public page tree under Home, section by section.

Each `*_body(ref)` returns the page's StreamField in frontend render order.
`ref` resolves seed keys: `ref.image(key)`, `ref.destination(slug)`,
`ref.package(slug)` (all return primary keys).
"""

from apps.seed.data.blocks import block, button, heading, link, reserve_cta, section

HOME = {
    "title": "Home",
    "slug": "home",
    "seo_title": "Lumora Treks | Travel Beyond Destinations",
    "search_description": (
        "Discover expertly crafted itineraries, local experiences, and seamless bookings that "
        "turn every journey into a story worth telling."
    ),
}

PACKAGE_CATEGORIES = [
    "Trekking",
    "Trail Run",
    "Hiking",
    "Day Excursions",
    "Religious Tour",
    "Nepal's Wild Life",
    "6000m Peak Climbing",
    "Sightseeing",
    "Paragliding",
]

FAQ_ITEMS = [
    {
        "question": "How do I book a trip?",
        "answer": (
            "<p>Choose a package and select <b>Reserve Now</b>, or send us an enquiry. We confirm "
            "availability, the price for your group size and payment details before anything is "
            "booked.</p>"
        ),
        "open_by_default": True,
    },
    {
        "question": "Can you tailor a package to my dates or group?",
        "answer": (
            "<p>Yes. Every itinerary can be adjusted to your dates, pace and group size — tell us "
            "what you have in mind in the enquiry form.</p>"
        ),
        "open_by_default": False,
    },
    {
        "question": "How can I reach you?",
        "answer": (
            "<p>Email hello@lumoratreks.com, call +977 1 4000000 or message us on WhatsApp. We reply "
            "within one business day.</p>"
        ),
        "open_by_default": False,
    },
    {
        "question": "Where is your office?",
        "answer": "<p>Our team is based in Thamel, Kathmandu, Nepal.</p>",
        "open_by_default": False,
    },
    {
        "question": "Do I need travel insurance?",
        "answer": (
            "<p>Yes. Travellers are responsible for insurance appropriate to their trip, as set out "
            "in our Terms &amp; Conditions.</p>"
        ),
        "open_by_default": False,
    },
]


def faq_section(anchor_id="faq"):
    return block(
        "faq",
        heading=heading("Frequently Asked Questions", "These are the questions we hear most often."),
        items=FAQ_ITEMS,
        show_side_card=True,
        side_card_heading="Don't see the answer you need?",
        side_card_text="That's ok. Just drop a message and we will get back to you as soon as possible.",
        side_card_button=button("Contact Us", "/contact", style="secondary"),
        settings=section(anchor_id),
    )


def hero_slide(ref, image, alt, destination, foreground=None):
    return {
        "image": ref.image(image),
        "foreground": ref.image(foreground) if foreground else None,
        "video": None,
        "alt": alt,
        "heading_override": "",
        "destination": ref.destination(destination),
    }


def destination_card(ref, slug, image, variant="default", layout="small", description=""):
    return {
        "destination": ref.destination(slug),
        "title": "",
        "description": description,
        "image": ref.image(image),
        "variant": variant,
        "layout": layout,
        "link": link(),
    }


# --------------------------------------------------------------------- home


def home_body(ref):
    return [
        block(
            "hero",
            heading="Travel beyond destinations",
            subheading="Creating lifelong memories",
            slides=[
                # The designed scene: the cut-out peaks are drawn in front of the heading.
                hero_slide(
                    ref, "hero-scene", "Snow-capped mountain landscape", "annapurna-circuit", foreground="hero-cutout"
                ),
                hero_slide(ref, "everest-region", "Ama Dablam in the Everest region", "everest-region"),
                hero_slide(ref, "annapurna-region", "Annapurna South above Ghandruk", "annapurna-region"),
                hero_slide(ref, "pokhara", "Phewa Lake and the Annapurna range", "pokhara"),
            ],
            show_search=True,
            search_location_label="Location",
            search_location_placeholder="Location",
            search_button_label="Search",
            settings=section("hero", container="full"),
        ),
        block(
            "intro_stats",
            heading="We've helped thousands of travelers discover unforgettable journeys across the world",
            highlight="unforgettable journeys",
            description=(
                "From iconic landmarks to hidden gems, we curate authentic travel experiences that "
                "inspire exploration, create lasting memories, and make every journey seamless from "
                "start to finish."
            ),
            description_highlight="and make every journey seamless from start to finish.",
            stats=[
                {"value": "24K+", "label": "Happy Travelers", "icon": ""},
                {"value": "120", "label": "Curated Destinations", "icon": ""},
                {"value": "4.9", "label": "Overall Ratings", "icon": ""},
            ],
            settings=section("about", container="narrow"),
        ),
        block(
            "popular_packages",
            heading=heading(
                "Popular Packages",
                "Explore our most loved travel packages, crafted for adventurers who want more than just a trip.",
                eyebrow="Handpicked For You",
            ),
            source="popular",
            packages=[],
            destination=None,
            sdk_package_ids=[],
            limit=8,
            autoplay=False,
            show_price=True,
            cta=button(),
            settings=section("packages"),
        ),
        block(
            "experience_showcase",
            heading="Discover the soul of Nepal with the warm hospitality of Lumora Treks",
            description=(
                "From the snow-capped Himalayas to ancient heritage cities and lush wildlife reserves, "
                "every destination is carefully selected to offer authentic experiences, breathtaking "
                "scenery, and unforgettable memories."
            ),
            description_highlight="offer authentic experiences, breathtaking scenery, and unforgettable memories.",
            show_arrows=True,
            small_cards=[
                destination_card(ref, "patan", "patan"),
                destination_card(ref, "pokhara", "pokhara"),
                destination_card(ref, "rara-lake", "rara-lake"),
            ],
            feature_card=destination_card(
                ref,
                "dhorpatan-region",
                "dhorpatan-meadow",
                variant="big-package",
                layout="large",
                description=(
                    "Escape into Nepal's only hunting reserve, where rolling alpine meadows, peaceful "
                    "villages, and panoramic mountain views create the perfect off-the-beaten-path adventure."
                ),
            ),
            settings=section("experience"),
        ),
        block(
            "why_choose_us",
            heading=heading(
                "Why Lumora Treks?",
                "We make every journey effortless, memorable, and uniquely yours. From carefully curated "
                "destinations to trusted local expertise, we're committed to delivering travel "
                "experiences that go beyond expectations.",
            ),
            description_highlight="we're committed to delivering travel experiences that go beyond expectations.",
            cards=[
                {
                    "theme": "light",
                    "heading": "Curated Destinations",
                    "heading_highlight": "",
                    "description": (
                        "Every destination is handpicked to showcase the best of nature, culture, and "
                        "adventure, ensuring every trip is truly unforgettable."
                    ),
                    "description_highlight": "",
                    "image": ref.image("machhapuchhre-sunrise"),
                    "link": link(),
                },
                {
                    "theme": "dark",
                    "heading": "Seamless Travel Planning",
                    "heading_highlight": "",
                    "description": (
                        "From personalized itineraries and accommodations to transportation and local "
                        "experiences, we handle every detail so you can simply enjoy the journey."
                    ),
                    "description_highlight": "",
                    "image": ref.image("teahouse"),
                    "link": link(),
                },
                {
                    "theme": "light",
                    "heading": "Trusted Local Expertise",
                    "heading_highlight": "",
                    "description": (
                        "Travel with confidence through experienced local guides, reliable partners, and "
                        "insider recommendations that help you discover destinations like never before."
                    ),
                    "description_highlight": "",
                    "image": ref.image("trekkers-guide"),
                    "link": link(),
                },
            ],
            settings=section("why-us"),
        ),
        block(
            "bento_grid",
            heading=heading(
                "Explore famous destinations",
                "Whether you're seeking mountain adventures or wildlife encounters.",
                align="left",
            ),
            variant="welcome",
            source="selected",
            items=[
                destination_card(ref, "dhorpatan-region", "dhorpatan-region"),
                destination_card(ref, "poon-hill", "poon-hill", variant="big-package", layout="large"),
                destination_card(ref, "annapurna-region", "annapurna-region"),
                destination_card(ref, "chitwan-safari", "chitwan"),
                destination_card(ref, "kathmandu", "kathmandu"),
            ],
            limit=6,
            settings=section("regions"),
        ),
        block(
            "authentic_experiences",
            heading="Discover Nepal Through Authentic Experiences with Us",
            description=(
                "From the majestic Himalayas and ancient heritage sites to serene lakes and vibrant local "
                "cultures, Lumora Treks helps you experience Nepal beyond the ordinary."
            ),
            description_highlight="Lumora Treks helps you experience Nepal beyond the ordinary.",
            image=ref.image("authentic-nepal"),
            reversed=False,
            items=[
                {
                    "number": "01",
                    "title": "Authentic Experiences",
                    "description": (
                        "Go beyond tourist attractions and immerse yourself in local cultures, "
                        "traditions, and hidden gems."
                    ),
                },
                {
                    "number": "02",
                    "title": "Hassle-Free Planning",
                    "description": (
                        "From accommodations to transportation, we handle every detail so you can "
                        "focus on making memories."
                    ),
                },
                {
                    "number": "03",
                    "title": "Safe & Reliable Travel",
                    "description": (
                        "Enjoy peace of mind with verified travel partners, expert guidance, and "
                        "dedicated support throughout your journey."
                    ),
                },
            ],
            settings=section("features"),
        ),
        faq_section(),
        reserve_cta("contact", ref),
    ]


# ------------------------------------------------------------ listing pages


def packages_index(ref):
    return {
        "title": "Packages",
        "slug": "packages",
        "intro": "Browse trips by style, destination, and travel pace.",
        "packages_per_page": 6,
        "show_filters": True,
        "body": [
            block(
                "page_hero",
                title="Discover your next adventure",
                subtitle="Choose from carefully crafted journeys across Nepal.",
                image=ref.image("packages-hero"),
                image_alt="Nepal travel experiences",
                image_width=565,
                image_height=457,
                show_search=True,
                settings=section("hero"),
            ),
            block(
                "package_listing",
                heading="Popular Packages",
                categories=PACKAGE_CATEGORIES,
                page_size=6,
                default_category="Trekking",
                show_filters=True,
                settings=section("packages"),
            ),
            block(
                "cultural_tours",
                heading="Cultural & Day Tours",
                description="Discover Nepal's heritage, food, and local stories.",
                source="selected",
                packages=[ref.package("pokhara-kathmandu-tours"), ref.package("journey-to-fish-lake")],
                destination=None,
                sdk_package_ids=[],
                limit=6,
                autoplay=False,
                show_price=True,
                cta=button(),
                settings=section("cultural-tours"),
            ),
            reserve_cta("packages-cta", ref),
        ],
    }


def destinations_index(ref):
    return {
        "title": "Destinations",
        "slug": "destinations",
        "intro": "Explore the places that make Nepal unforgettable.",
        "body": [
            block(
                "page_hero",
                title="Explore Nepal's remarkable destinations",
                subtitle="From high Himalayan trails to living heritage cities.",
                image=ref.image("destinations-hero"),
                image_alt="Nepal destinations",
                image_width=565,
                image_height=457,
                show_search=True,
                settings=section("hero"),
            ),
            block(
                "destinations_grid",
                heading="Our Destinations",
                source="featured",
                destinations=[],
                limit=12,
                settings=section("destinations"),
            ),
            reserve_cta("destinations-cta", ref),
        ],
    }


def destination_detail_body(ref):
    tight = {"spacing": "none"}
    return [
        block("destination_header", settings=section("destination-header", **tight)),
        block("destination_overview", settings=section("destination-overview", **tight)),
        block("destination_packages", settings=section("destination-packages", **tight)),
    ]


# ------------------------------------------------------------ single pages


def contact(ref):
    return {
        "title": "Contact Us",
        "slug": "contact",
        "intro": "Get in touch with Lumora Treks.",
        "body": [
            block("contact_hero", image=ref.image("contact-hero"), settings=section("contact-hero")),
            block(
                "contact_form",
                heading="Don't Hesitate to Contact Us",
                heading_highlight="Contact Us",
                description=(
                    "Whether you have a quick question or want to book a full consultation — we're easy "
                    "to reach. Fill in the form and we'll respond within one business day"
                ),
                description_highlight="Fill in the form and we'll respond within one business day",
                socials=[
                    {"icon": "mdi:facebook", "label": "Facebook", "url": "https://www.facebook.com/LumoraTreks"},
                    {"icon": "mdi:instagram", "label": "Instagram", "url": "https://www.instagram.com/lumoratreks/"},
                    {"icon": "mdi:whatsapp", "label": "WhatsApp", "url": "https://wa.me/9779847259352"},
                ],
                destinations=[
                    ref.destination(slug)
                    for slug in ("annapurna-region", "everest-region", "kathmandu", "pokhara", "chitwan-safari")
                ],
                submit_label="Reserve Now",
                settings=section("contact-form"),
            ),
            faq_section(),
        ],
    }


def privacy(ref):
    return {
        "title": "Privacy Policy",
        "slug": "privacy",
        "intro": "How Lumora Treks handles your personal information.",
        "body": [
            block(
                "rich_text",
                heading="Privacy Policy",
                body=(
                    "<h2>Information we collect</h2><p>We collect the information you provide when you "
                    "contact us, request a trip, or make a booking.</p><h2>How we use your "
                    "information</h2><p>We use it to respond to enquiries, arrange travel, provide "
                    "support, and meet legal obligations.</p><h2>Your choices</h2><p>You may request "
                    "access to, correction of, or deletion of your personal information, subject to "
                    "applicable obligations.</p>"
                ),
                width="narrow",
                settings=section("privacy"),
            )
        ],
    }


def terms(ref):
    return {
        "title": "Terms & Conditions",
        "slug": "terms",
        "intro": "The terms that apply to trips booked with Lumora Treks.",
        "body": [
            block(
                "rich_text",
                heading="Terms & Conditions",
                body=(
                    "<h2>Booking and payment</h2><p>By booking a trip with Lumora Treks you agree to the "
                    "deposit, balance, and payment terms communicated at the time of booking.</p>"
                    "<h2>Cancellations and changes</h2><p>Cancellation and amendment charges vary by "
                    "trip and season; the applicable terms are shared before you confirm.</p>"
                    "<h2>Travel insurance and responsibility</h2><p>Travellers are responsible for "
                    "appropriate insurance, valid documentation, and following guide instructions "
                    "during the trip.</p><h2>Liability</h2><p>Lumora Treks is not liable for delays or "
                    "changes caused by weather, force majeure, or circumstances beyond our reasonable "
                    "control.</p>"
                ),
                width="narrow",
                settings=section("terms"),
            )
        ],
    }


def enquiry(ref):
    return {
        "title": "Enquiry",
        "slug": "enquiry",
        "body": [block("package_enquiry", package=None, settings=section("enquiry"))],
    }


def checkout(ref):
    return {
        "title": "Checkout",
        "slug": "checkout",
        "body": [block("checkout", settings=section("checkout"))],
    }


def payment_success(ref):
    return {
        "title": "Payment Success",
        "slug": "success",
        "body": [block("payment_success", settings=section("payment-success"))],
    }
