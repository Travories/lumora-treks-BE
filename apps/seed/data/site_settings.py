"""Brand, navigation and footer settings (Site settings in the admin)."""

from apps.seed.data.blocks import button, link

BRAND = {
    "site_name": "Lumora Treks",
    "tagline": "Travel beyond destinations",
    "logo_icon": "ph:mountains-fill",
    "default_meta_title": "Lumora Treks | Travel Beyond Destinations",
    "default_meta_description": (
        "Discover expertly crafted itineraries, local experiences, and seamless bookings that turn "
        "every journey into a story worth telling."
    ),
    "email": "hello@lumoratreks.com",
    "phone": "+977 1 4000000",
    "whatsapp": "+977 9847259352",
    "address": "Thamel, Kathmandu, Nepal",
}


def _nav_item(label, url):
    return {"type": "item", "value": {**link(label, url), "icon": "", "children": [], "highlight": False}}


NAVIGATION = {
    "items": [
        _nav_item("Home", "/"),
        _nav_item("Packages", "/packages"),
        _nav_item("Destinations", "/destinations"),
        _nav_item("Blog", "/blog"),
        _nav_item("Contact Us", "/contact"),
    ],
    "cta_button": [{"type": "button", "value": button("Reserve Now", "/enquiry", style="secondary", size="sm")}],
    "sticky": True,
}

FOOTER = {
    "description": (
        "Your trusted travel partner in Nepal. We curate authentic experiences, breathtaking "
        "destinations, and unforgettable memories."
    ),
    "columns": [
        {
            "type": "column",
            "value": {
                "heading": "",
                "links": [
                    link("Contact Us", "/contact"),
                    link("FAQs", "/contact#faq"),
                    link("Privacy Policy", "/privacy"),
                    link("Terms & Conditions", "/terms"),
                ],
            },
        }
    ],
    "socials": [
        {"type": "social", "value": {"platform": "Facebook", "icon": "mdi:facebook", "url": "https://www.facebook.com/LumoraTreks"}},
        {"type": "social", "value": {"platform": "Instagram", "icon": "mdi:instagram", "url": "https://www.instagram.com/lumoratreks/"}},
        {"type": "social", "value": {"platform": "WhatsApp", "icon": "mdi:whatsapp", "url": "https://wa.me/9779847259352"}},
    ],
    "newsletter_enabled": True,
    "newsletter_heading": "Newsletter",
    "newsletter_text": "Subscribe to get the latest travel deals and stories.",
    "secondary_text": "Designed & built with care for travelers everywhere.",
}
