"""Small builders for StreamField block values used across the seed pages."""


def section(anchor_id="", background="default", spacing="md", container="default"):
    """The `settings` struct every section block carries."""
    return {
        "anchor_id": anchor_id,
        "background": background,
        "spacing": spacing,
        "container": container,
        "hidden": False,
    }


def link(label="", url=""):
    return {
        "label": label,
        "link_type": "url",
        "page": None,
        "url": url,
        "anchor": "",
        "document": None,
        "email": "",
        "phone": "",
        "open_in_new_tab": False,
    }


def button(label="", url="", style="primary", size="md"):
    return {**link(label, url), "style": style, "size": size, "icon": ""}


def heading(text, description="", eyebrow="", align="center"):
    return {"eyebrow": eyebrow, "heading": text, "description": description, "align": align}


def block(block_type, **value):
    return {"type": block_type, "value": value}


def reserve_cta(anchor_id, ref, container="full", spacing="md"):
    """The "Reserve Now" banner that closes most pages."""
    return block(
        "cta_banner",
        heading="Create memories that stay with you long after the Journey Ends",
        text="",
        background_image=ref.image("cta-bg"),
        buttons=[button("Reserve Now", "/enquiry")],
        settings=section(anchor_id, container=container, spacing=spacing),
    )
