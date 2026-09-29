"""
The Lumora guide — how to run the website from Lumora Admin (Help › Lumora guide).

Content lives here as plain data so it's easy to keep in step with the admin.
Each section pairs numbered steps with media from `static/lumora_admin/guide/`:
a still of the part of the website being changed and an animation of doing it
in the admin. Re-record the media when the admin or the site changes visibly.
"""

from django.urls import reverse_lazy
from django.views.generic import TemplateView
from wagtail.admin.views.generic import WagtailAdminTemplateMixin

GUIDE = [
    {
        "id": "find-your-way",
        "icon": "home",
        "title": "Find your way around",
        "summary": "What lives where in the sidebar.",
        "intro": (
            "Everything on the website is edited from the sidebar. Content you change often is at the "
            "top; settings that affect the whole site are further down."
        ),
        "points": [
            ("Pages", "The website's pages — Home, Packages, Destinations, Contact and more — and their sections."),
            ("Blog", "Every story in one list. Write, edit and publish posts."),
            ("Packages", "Trips: price, itinerary, gallery, inclusions and group pricing."),
            ("Destinations", "Places, with their photo, region, season and highlights."),
            ("Testimonials", "Traveller quotes shown on the site and on packages."),
            ("Leads", "Enquiries and newsletter sign-ups sent from the website."),
            ("Media", "Images, videos and documents used across the site."),
            ("Site settings", "Brand and contact details, navigation, footer, theme and integrations."),
        ],
        "media": [
            {"file": "dashboard.webp", "caption": "The dashboard and sidebar in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "edit-a-page",
        "icon": "doc-empty-inverse",
        "title": "Edit a page — for example the Home hero",
        "summary": "Change the text and images of any section on any page.",
        "intro": (
            "Every page is built from sections, listed in the same order as they appear on the website. "
            "The Home page's first section is the hero."
        ),
        "steps": [
            "Go to <b>Pages</b> and open <b>Home</b>.",
            "Switch to the <b>Page layout</b> tab — it lists every section of the page, top to bottom.",
            "Open the <b>Hero</b> section and change the heading, subheading or slides.",
            "Watch the counter under each field: it shows how many characters fit the design.",
            "Click <b>Publish</b> to update the website, or <b>Save draft</b> to finish later.",
        ],
        "tip": "Use the arrows on a section to move it up or down, or the bin to remove it from the page.",
        "media": [
            {"file": "home-hero-website.webp", "caption": "The hero on the website", "kind": "website"},
            {"file": "home-hero-admin.webp", "caption": "Editing the hero in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "add-a-package",
        "icon": "tag",
        "title": "Add a package",
        "summary": "Create a trip with its itinerary and pricing.",
        "intro": (
            "A package holds everything about a trip. Its page on the website is created automatically "
            "the first time you save it."
        ),
        "steps": [
            "Go to <b>Packages</b> and click <b>Add package</b>.",
            "On <b>Overview</b>, fill in the title, category, destination, summary, description and cover image.",
            "On <b>Pricing &amp; facts</b>, set the price, group pricing and trip facts.",
            "On <b>Itinerary &amp; inclusions</b>, add each day — with where travellers stay, eat and how they travel — "
            "and what is included or not.",
            "Add photos on <b>Gallery</b>, then click <b>Save</b>.",
        ],
        "tip": (
            "After saving, the <b>Related content</b> panel at the top links to the package's page, its destination "
            "and its enquiries."
        ),
        "media": [
            {"file": "package-website.webp", "caption": "A package page on the website", "kind": "website"},
            {"file": "add-package-admin.webp", "caption": "Adding a package in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "write-a-blog-post",
        "icon": "doc-full",
        "title": "Write a blog post",
        "summary": "Publish a story or travel guide.",
        "intro": "Stories appear on the Blog page, newest first; the one marked Featured is shown large at the top.",
        "steps": [
            "Go to <b>Blog</b> and click <b>Add blog post</b>.",
            "On <b>Story</b>, write the title and excerpt, choose a hero image and write the article.",
            "On <b>Publishing details</b>, pick the category, date and author.",
            "Click <b>Publish</b> — or <b>Save draft</b> to come back to it.",
        ],
        "media": [
            {"file": "blog-website.webp", "caption": "A blog post on the website", "kind": "website"},
            {"file": "add-blog-admin.webp", "caption": "Writing a blog post in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "add-a-destination",
        "icon": "globe",
        "title": "Add a destination",
        "summary": "Places travellers can explore, and the packages that go there.",
        "intro": "Destinations are shown in the destination grids and on their own page.",
        "steps": [
            "Go to <b>Destinations</b> and click <b>Add destination</b>.",
            "Fill in the title, subtitle, description, highlights (one per line) and photo.",
            "Set the region and best season, then click <b>Save</b>.",
            "To link a trip to it, open the package and choose this destination on its Overview.",
        ],
        "media": [
            {"file": "destination-website.webp", "caption": "A destination page on the website", "kind": "website"},
            {"file": "destination-admin.webp", "caption": "A destination in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "menus-footer-contact",
        "icon": "sliders",
        "title": "Change menus, footer and contact details",
        "summary": "Site-wide content: navigation, footer, email and phone.",
        "intro": "Anything shown on every page is edited once, under Site settings.",
        "steps": [
            "Go to <b>Site settings</b>.",
            "<b>Navigation</b> — the links at the top of every page and the button beside them.",
            "<b>Footer</b> — the description, link columns, social links and copyright line.",
            "<b>Brand &amp; contact</b> — site name, tagline, email, phone, WhatsApp and address.",
            "Click <b>Save</b>; the change appears on every page.",
        ],
        "media": [
            {"file": "footer-website.webp", "caption": "The footer on the website", "kind": "website"},
            {"file": "footer-admin.webp", "caption": "Footer settings in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "images",
        "icon": "image",
        "title": "Add images",
        "summary": "Upload photos once and use them anywhere.",
        "intro": (
            "Upload large, sharp photos — the website automatically serves each one at the right size for the "
            "visitor's screen."
        ),
        "steps": [
            "Go to <b>Media › Images</b> and click <b>Add an image</b>, or upload straight from any image field.",
            "Give every image <b>Alt text</b> — a short description for screen readers and search engines.",
            "Fill in <b>Credit</b> with the photographer or source when the photo isn't yours.",
        ],
        "media": [
            {"file": "images-admin.webp", "caption": "The image library in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "leads",
        "icon": "mail",
        "title": "Handle enquiries",
        "summary": "Follow up on messages from the website.",
        "intro": "Every enquiry and newsletter sign-up from the website arrives in Leads.",
        "steps": [
            "Go to <b>Leads</b> — the newest are at the top; filter by status or package.",
            "Open a lead to read the message and contact details.",
            "Set its <b>Status</b> (New, Contacted, Converted or Spam) and add notes, then click <b>Save</b>.",
        ],
        "media": [
            {"file": "leads-admin.webp", "caption": "Leads in Lumora Admin", "kind": "admin"},
        ],
    },
    {
        "id": "good-to-know",
        "icon": "help",
        "title": "Good to know",
        "summary": "Small things that make editing easier.",
        "points": [
            ("Character counters", "Short text fields show how many characters fit the design. Keep within them."),
            ("Long descriptions", "Package and destination descriptions have no limit — the website adds a "
             "“Show more” button when they are long."),
            ("View live", "The eye icon at the top of a page opens it on the website."),
            ("Drafts and history", "Save draft keeps changes private until you publish; the clock icon shows every "
             "earlier version, which you can restore."),
            ("Search", "The search at the top of the sidebar finds pages; each list also has its own search."),
        ],
    },
]


class GuideView(WagtailAdminTemplateMixin, TemplateView):
    page_title = "Lumora guide"
    header_icon = "help"
    template_name = "core/guide.html"
    breadcrumbs_items = [
        {"url": reverse_lazy("wagtailadmin_home"), "label": "Home"},
        {"url": "", "label": "Lumora guide"},
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = GUIDE
        return context
