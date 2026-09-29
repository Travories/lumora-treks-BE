"""The Blog index page and its stories."""

from datetime import date

from apps.seed.data.blocks import block, reserve_cta, section

AUTHORS = {
    "aarav": ("Aarav Thapa", "Lead Guide"),
    "mira": ("Mira Gurung", "Travel Writer"),
    "kiran": ("Kiran Rai", "Culture Editor"),
}

POSTS = [
    {
        "slug": "annapurna-the-case-for-going-slow",
        "title": "Annapurna: The Case for Going Slow",
        "excerpt": (
            "Why the most rewarding way through the Annapurna region isn't the fastest one — "
            "a field guide to walking with intention."
        ),
        "image": "pkg-annapurna",
        "category": "Trekking",
        "author": "aarav",
        "featured": True,
        "published": date(2026, 8, 28),
        "read_minutes": 8,
    },
    {
        "slug": "a-morning-in-kathmandu-durbar-square",
        "title": "A Morning in Kathmandu Durbar Square",
        "excerpt": (
            "Temples, courtyards, and living history — how to experience the old heart of the "
            "city before the crowds arrive."
        ),
        "image": "dest-kathmandu",
        "category": "Culture",
        "author": "kiran",
        "featured": False,
        "published": date(2026, 8, 19),
        "read_minutes": 6,
    },
    {
        "slug": "what-to-eat-on-the-trail",
        "title": "What to Eat on the Trail: A Tea-House Menu",
        "excerpt": "Dal bhat power, garlic soup for altitude, and the quiet ritual of milk tea at 3,000 metres.",
        "image": "exp-patan",
        "category": "Food & Stays",
        "author": "mira",
        "featured": False,
        "published": date(2026, 8, 11),
        "read_minutes": 5,
    },
    {
        "slug": "the-poon-hill-sunrise-is-worth-the-alarm",
        "title": "The Poon Hill Sunrise Is Worth the Alarm",
        "excerpt": "A 4am start, a candle-lit climb, and one of the most generous mountain panoramas in the world.",
        "image": "dest-poonhills",
        "category": "Trekking",
        "author": "aarav",
        "featured": False,
        "published": date(2026, 7, 30),
        "read_minutes": 4,
    },
    {
        "slug": "the-only-packing-list-you-need",
        "title": "The Only Himalayan Packing List You Need",
        "excerpt": "Layers, not luggage. Everything that earns its place in your pack — and the things that don't.",
        "image": "pkgp-4",
        "category": "Guides",
        "author": "mira",
        "featured": False,
        "published": date(2026, 7, 18),
        "read_minutes": 7,
    },
    {
        "slug": "staying-with-a-family-in-ghandruk",
        "title": "Staying With a Family in Ghandruk",
        "excerpt": (
            "What a night in a Gurung homestay taught us about hospitality, and why we build it "
            "into every trip."
        ),
        "image": "exp-dhorpatan",
        "category": "Culture",
        "author": "kiran",
        "featured": False,
        "published": date(2026, 7, 5),
        "read_minutes": 6,
    },
    {
        "slug": "when-is-the-best-time-to-trek-nepal",
        "title": "When Is the Best Time to Trek in Nepal?",
        "excerpt": (
            "Autumn clarity vs. spring blooms vs. quiet-season solitude — an honest "
            "month-by-month breakdown."
        ),
        "image": "dest-annapurna",
        "category": "Guides",
        "author": "aarav",
        "featured": False,
        "published": date(2026, 6, 22),
        "read_minutes": 9,
    },
]

INDEX = {
    "title": "Blog",
    "slug": "blog",
    "intro": "Field notes and trekking guides from the trail.",
    "seo_title": "Stories & Guides | Lumora Treks",
    "search_description": "Field notes, trekking guides, and cultural stories from the Himalaya.",
}


def index_body(ref):
    return [
        block(
            "page_hero",
            title="Stories & Guides",
            subtitle="Field notes and trekking guides from the trail — stories worth carrying home.",
            image=ref.image("exp-big"),
            image_alt="Himalayan trail at golden hour",
            image_width=620,
            image_height=460,
            show_search=False,
            settings=section("blog-hero"),
        ),
        block(
            "blog_listing",
            heading="Latest stories",
            categories=["All", "Trekking", "Culture", "Food & Stays", "Guides"],
            page_size=5,
            show_featured=True,
            settings=section("blog"),
        ),
        reserve_cta("blog-cta", ref),
    ]


def post_body(ref):
    """Screen layout of a story page; the prose lives in `article_body`."""
    full = {"spacing": "none", "container": "full"}
    return [
        block("blog_article_header", settings=section("article-header", **full)),
        block("blog_article_body", settings=section("article", **full)),
        block("blog_related_stories", heading="Keep reading", count=3, settings=section("related-stories", **full)),
        reserve_cta("article-cta", ref, spacing="none"),
    ]


def article_body(title, ref):
    return [
        {
            "type": "paragraph",
            "value": (
                f"<p>{title} begins the way every great Himalayan journey does — early, cold, and "
                "quietly hopeful. Before the sun crests the ridgeline, the trail is yours alone, and "
                "the mountains feel less like a destination and more like a conversation you are only "
                "just beginning.</p>"
            ),
        },
        {
            "type": "paragraph",
            "value": (
                "<p>We designed this route to slow you down. Fewer kilometres, more moments: a tea "
                "house where the owner remembers your name, a pass that opens onto a valley no "
                "photograph does justice, a night sky so dense with stars it feels close enough to "
                "touch.</p>"
            ),
        },
        {"type": "heading", "value": "When to go"},
        {
            "type": "paragraph",
            "value": (
                "<p>Autumn (late September to November) brings the clearest skies and the sharpest "
                "mountain views, while spring (March to May) trades a little haze for hillsides of "
                "blooming rhododendron. Both seasons are kind to first-time trekkers.</p>"
            ),
        },
        {
            "type": "image",
            "value": {
                "image": ref.image("exp-big"),
                "alt": "Golden light over the Himalayan foothills",
                "caption": "First light on the ridge — the reward for an early start.",
            },
        },
        {"type": "heading", "value": "What makes it different"},
        {
            "type": "paragraph",
            "value": (
                "<p>This isn't a race to the highest point. It's a route built around the people and "
                "places along the way — local homestays over anonymous lodges, seasonal food over "
                "packaged meals, and guides who grew up on these trails.</p>"
            ),
        },
        {
            "type": "quote",
            "value": {
                "text": (
                    "You don't conquer a mountain. You are simply allowed, for a few days, to walk "
                    "in its company."
                ),
                "cite": "A saying from the trail",
            },
        },
        {
            "type": "paragraph",
            "value": (
                "<p>By the time you descend, something has shifted. The photos will be beautiful — "
                "they always are — but what stays with you is quieter: the rhythm of your own "
                "footsteps, the warmth of shared tea, the particular silence of high places.</p>"
            ),
        },
    ]
