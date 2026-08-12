"""
Shared block primitives.

The default Wagtail chooser blocks serialize to a bare id, which is useless to
a decoupled frontend. Every chooser here is subclassed to emit a full object
(URLs, renditions, alt text, resolved hrefs) so a single API call gives the
frontend everything it needs to render.
"""

from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.exceptions import EmbedException
from wagtail.images.blocks import ImageChooserBlock
from wagtail.rich_text import expand_db_html
from wagtail.snippets.blocks import SnippetChooserBlock

from apps.core.serializers import (
    serialize_document,
    serialize_image,
    serialize_page_ref,
    serialize_video,
)

RICH_TEXT_FEATURES = [
    "h2",
    "h3",
    "h4",
    "bold",
    "italic",
    "ol",
    "ul",
    "hr",
    "link",
    "document-link",
    "image",
    "embed",
    "blockquote",
    "superscript",
    "subscript",
]


class APIImageChooserBlock(ImageChooserBlock):
    """Image chooser that serializes to `{url, alt, renditions, ...}`."""

    def get_api_representation(self, value, context=None):
        return serialize_image(value)


class APIDocumentChooserBlock(DocumentChooserBlock):
    def get_api_representation(self, value, context=None):
        return serialize_document(value)


class APIPageChooserBlock(blocks.PageChooserBlock):
    def get_api_representation(self, value, context=None):
        return serialize_page_ref(value)


class VideoChooserBlock(SnippetChooserBlock):
    """Chooser for the Video snippet, serialized with playback settings."""

    def __init__(self, **kwargs):
        kwargs.setdefault("icon", "media")
        super().__init__("core.Video", **kwargs)

    def get_api_representation(self, value, context=None):
        return serialize_video(value)


class APIRichTextBlock(blocks.RichTextBlock):
    """Rich text with internal `<embed>`/`<a linktype>` tags already expanded."""

    def __init__(self, **kwargs):
        kwargs.setdefault("features", RICH_TEXT_FEATURES)
        super().__init__(**kwargs)

    def get_api_representation(self, value, context=None):
        if not value:
            return ""
        return expand_db_html(value.source)


class APIEmbedBlock(EmbedBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        data = {"url": value.url, "html": None, "provider": None, "title": None}
        try:
            embed = get_embed(value.url)
        except EmbedException:
            return data
        data.update(
            {
                "html": embed.html,
                "provider": embed.provider_name,
                "title": embed.title,
                "width": embed.width,
                "height": embed.height,
                "thumbnail": embed.thumbnail_url,
            }
        )
        return data


class IconBlock(blocks.CharBlock):
    """
    An Iconify icon name (e.g. `iconoir:arrow-right`) — the frontend already
    renders icons with @iconify/react, so the CMS just stores the name.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault("help_text", "Iconify icon name, e.g. iconoir:arrow-right")
        super().__init__(**kwargs)


class LinkBlock(blocks.StructBlock):
    """
    One link that can point at a CMS page, an external URL, an on-page anchor,
    a document, an email or a phone number. The API resolves it to a single
    `href` so the frontend never has to branch on link type.
    """

    LINK_TYPES = [
        ("page", "CMS page"),
        ("url", "External URL"),
        ("anchor", "Anchor on this page"),
        ("document", "Document"),
        ("email", "Email address"),
        ("phone", "Phone number"),
    ]

    label = blocks.CharBlock(required=False, max_length=80)
    link_type = blocks.ChoiceBlock(choices=LINK_TYPES, default="page")
    page = APIPageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)
    anchor = blocks.CharBlock(required=False, max_length=80, help_text="Without the '#'.")
    document = APIDocumentChooserBlock(required=False)
    email = blocks.EmailBlock(required=False)
    phone = blocks.CharBlock(required=False, max_length=40)
    open_in_new_tab = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "link"
        label = "Link"
        form_classname = "struct-block link-block"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        if data is None:
            return None
        data["href"] = self._resolve_href(value)
        return data

    @staticmethod
    def _resolve_href(value):
        link_type = value.get("link_type")
        if link_type == "page" and value.get("page"):
            return value["page"].get_url() or f"/{value['page'].slug}/"
        if link_type == "url":
            return value.get("url") or None
        if link_type == "anchor" and value.get("anchor"):
            return f"#{value['anchor'].lstrip('#')}"
        if link_type == "document" and value.get("document"):
            from apps.core.serializers import absolute_url

            return absolute_url(value["document"].url)
        if link_type == "email" and value.get("email"):
            return f"mailto:{value['email']}"
        if link_type == "phone" and value.get("phone"):
            return f"tel:{value['phone'].replace(' ', '')}"
        return None


class ButtonBlock(LinkBlock):
    """A link rendered as a button — matches the FE `<Button variant size />`."""

    style = blocks.ChoiceBlock(
        choices=[("primary", "Primary"), ("secondary", "Secondary"), ("outline", "Outline")],
        default="primary",
    )
    size = blocks.ChoiceBlock(
        choices=[("sm", "Small"), ("md", "Medium"), ("lg", "Large")],
        default="md",
    )
    icon = IconBlock()

    class Meta:
        icon = "link"
        label = "Button"


class SectionSettingsBlock(blocks.StructBlock):
    """
    Presentation options every section shares. Appended to the end of each
    section block so editors see content first, settings last.
    """

    anchor_id = blocks.CharBlock(
        required=False,
        max_length=60,
        help_text="Adds an id to the section so nav links like #packages can target it.",
    )
    background = blocks.ChoiceBlock(
        choices=[
            ("default", "Page background"),
            ("surface", "Surface (white)"),
            ("dark", "Dark (secondary)"),
            ("primary", "Brand green"),
        ],
        default="default",
    )
    spacing = blocks.ChoiceBlock(
        choices=[("none", "None"), ("sm", "Small"), ("md", "Medium"), ("lg", "Large")],
        default="md",
    )
    container = blocks.ChoiceBlock(
        choices=[("default", "Default (max-w-7xl)"), ("narrow", "Narrow"), ("full", "Full bleed")],
        default="default",
    )
    hidden = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Keep the section in the page but stop rendering it.",
    )

    class Meta:
        icon = "cogs"
        label = "Section settings"
        collapsed = True


class SectionBlock(blocks.StructBlock):
    """
    Base class for every registered section.

    Subclasses set `component` to the name of the React component that renders
    them; the API echoes it back as `component`, which is the contract the
    frontend's block registry keys off.
    """

    component = ""

    def __init__(self, local_blocks=None, **kwargs):
        local_blocks = list(local_blocks or [])
        local_blocks.append(("settings", SectionSettingsBlock()))
        super().__init__(local_blocks, **kwargs)

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        if isinstance(data, dict):
            data["component"] = self.component or self.name
        return data

    class Meta:
        icon = "placeholder"


class HeadingGroupBlock(blocks.StructBlock):
    """The eyebrow / heading / description trio used by most sections."""

    eyebrow = blocks.CharBlock(
        required=False,
        max_length=120,
        help_text="Small script-font line above the heading.",
    )
    heading = blocks.CharBlock(required=False, max_length=200)
    description = blocks.TextBlock(required=False)
    align = blocks.ChoiceBlock(
        choices=[("center", "Center"), ("left", "Left")],
        default="center",
    )

    class Meta:
        icon = "title"
        label = "Section heading"
