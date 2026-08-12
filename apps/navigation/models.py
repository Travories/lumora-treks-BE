"""
Site-wide settings: everything outside the page body is still CMS-managed —
navbar, footer, brand identity, theme colours and integrations.
"""

from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import StreamField

from apps.core.blocks import ButtonBlock, IconBlock, LinkBlock


class NavItemBlock(LinkBlock):
    """A top-level nav entry, optionally with a dropdown of children."""

    icon = IconBlock()
    children = blocks.ListBlock(LinkBlock(), required=False, default=[], label="Dropdown links")
    highlight = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "link"
        label = "Nav item"


class FooterColumnBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80)
    links = blocks.ListBlock(LinkBlock(), label="Links")

    class Meta:
        icon = "list-ul"
        label = "Footer column"


class SocialLinkBlock(blocks.StructBlock):
    platform = blocks.CharBlock(max_length=60, help_text="e.g. Facebook")
    icon = IconBlock(required=True, help_text="Iconify name, e.g. mdi:facebook")
    url = blocks.URLBlock()

    class Meta:
        icon = "site"
        label = "Social link"


@register_setting(icon="site")
class BrandSettings(BaseGenericSetting):
    """Logo, name and the copy that identifies the company."""

    site_name = models.CharField(max_length=120, default="Lumora Treks")
    tagline = models.CharField(max_length=250, blank=True)
    logo = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    logo_dark = models.ForeignKey(
        "core.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Used on dark backgrounds (footer).",
    )
    logo_icon = models.CharField(
        max_length=100,
        blank=True,
        default="ph:mountains-fill",
        help_text="Iconify name used when no logo image is set.",
    )
    favicon = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    default_share_image = models.ForeignKey(
        "core.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    default_meta_title = models.CharField(max_length=200, blank=True)
    default_meta_description = models.TextField(blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    map_embed_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("site_name"), FieldPanel("tagline")], heading="Identity"
        ),
        MultiFieldPanel(
            [
                FieldPanel("logo"),
                FieldPanel("logo_dark"),
                FieldPanel("logo_icon"),
                FieldPanel("favicon"),
            ],
            heading="Logo",
        ),
        MultiFieldPanel(
            [
                FieldPanel("default_meta_title"),
                FieldPanel("default_meta_description"),
                FieldPanel("default_share_image"),
            ],
            heading="Default SEO",
        ),
        MultiFieldPanel(
            [
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("whatsapp"),
                FieldPanel("address"),
                FieldPanel("map_embed_url"),
            ],
            heading="Contact",
        ),
    ]

    class Meta:
        verbose_name = "Brand & contact"


@register_setting(icon="list-ul")
class NavigationSettings(BaseGenericSetting):
    """→ `src/components/layout/Navbar.tsx`"""

    items = StreamField(
        [("item", NavItemBlock())],
        blank=True,
        verbose_name="Nav items",
    )
    cta_button = StreamField(
        [("button", ButtonBlock())], blank=True, max_num=1
    )
    sticky = models.BooleanField(default=True)
    announcement_text = models.CharField(
        max_length=250, blank=True, help_text="Optional bar above the navbar."
    )
    announcement_link = models.URLField(blank=True)

    panels = [
        FieldPanel("items"),
        FieldPanel("cta_button"),
        FieldPanel("sticky"),
        MultiFieldPanel(
            [FieldPanel("announcement_text"), FieldPanel("announcement_link")],
            heading="Announcement bar",
        ),
    ]

    class Meta:
        verbose_name = "Navigation"


@register_setting(icon="placeholder")
class FooterSettings(BaseGenericSetting):
    """→ `src/components/layout/Footer.tsx`"""

    description = models.TextField(blank=True)
    columns = StreamField([("column", FooterColumnBlock())], blank=True)
    socials = StreamField([("social", SocialLinkBlock())], blank=True)

    newsletter_enabled = models.BooleanField(default=True)
    newsletter_heading = models.CharField(max_length=120, blank=True, default="Newsletter")
    newsletter_text = models.CharField(max_length=250, blank=True)
    newsletter_placeholder = models.CharField(max_length=120, blank=True, default="Your email")
    newsletter_button_label = models.CharField(max_length=60, blank=True, default="Join")

    copyright_text = models.CharField(
        max_length=250,
        blank=True,
        help_text="{year} is replaced with the current year.",
        default="© {year} Lumora Treks. All rights reserved.",
    )
    secondary_text = models.CharField(max_length=250, blank=True)

    panels = [
        FieldPanel("description"),
        FieldPanel("columns"),
        FieldPanel("socials"),
        MultiFieldPanel(
            [
                FieldPanel("newsletter_enabled"),
                FieldPanel("newsletter_heading"),
                FieldPanel("newsletter_text"),
                FieldPanel("newsletter_placeholder"),
                FieldPanel("newsletter_button_label"),
            ],
            heading="Newsletter",
        ),
        MultiFieldPanel(
            [FieldPanel("copyright_text"), FieldPanel("secondary_text")], heading="Legal"
        ),
    ]

    class Meta:
        verbose_name = "Footer"


@register_setting(icon="colour-palette")
class ThemeSettings(BaseGenericSetting):
    """
    Design tokens mirroring `src/app/globals.css`, so brand colours are editable
    without a deploy. The frontend injects these as CSS custom properties.
    """

    background = models.CharField(max_length=20, default="#f5f5f5")
    surface = models.CharField(max_length=20, default="#ffffff")
    foreground = models.CharField(max_length=20, default="#1e1e1e")

    primary = models.CharField(max_length=20, default="#68bf4d")
    primary_hover = models.CharField(max_length=20, default="#59a941")
    primary_active = models.CharField(max_length=20, default="#4a9036")
    primary_accent = models.CharField(max_length=20, default="#8bff66")

    secondary = models.CharField(max_length=20, default="#1e1e1e")
    secondary_hover = models.CharField(max_length=20, default="#343434")
    secondary_active = models.CharField(max_length=20, default="#050505")

    text_primary = models.CharField(max_length=20, default="#1e1e1e")
    text_secondary = models.CharField(max_length=20, default="#47586e")
    text_muted = models.CharField(max_length=20, default="#546881")
    text_inverse = models.CharField(max_length=20, default="#f5f5f5")
    border = models.CharField(max_length=20, default="#e0e4e8")

    panels = [
        MultiFieldPanel(
            [FieldPanel("background"), FieldPanel("surface"), FieldPanel("foreground")],
            heading="Surfaces",
        ),
        MultiFieldPanel(
            [
                FieldPanel("primary"),
                FieldPanel("primary_hover"),
                FieldPanel("primary_active"),
                FieldPanel("primary_accent"),
            ],
            heading="Primary (brand green)",
        ),
        MultiFieldPanel(
            [FieldPanel("secondary"), FieldPanel("secondary_hover"), FieldPanel("secondary_active")],
            heading="Secondary (ink)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("text_primary"),
                FieldPanel("text_secondary"),
                FieldPanel("text_muted"),
                FieldPanel("text_inverse"),
                FieldPanel("border"),
            ],
            heading="Text & borders",
        ),
    ]

    class Meta:
        verbose_name = "Theme colours"

    @property
    def css_variables(self):
        return {
            "--background": self.background,
            "--surface": self.surface,
            "--foreground": self.foreground,
            "--color-primary": self.primary,
            "--color-primary-hover": self.primary_hover,
            "--color-primary-active": self.primary_active,
            "--color-primary-accent": self.primary_accent,
            "--color-secondary": self.secondary,
            "--color-secondary-hover": self.secondary_hover,
            "--color-secondary-active": self.secondary_active,
            "--color-text-primary": self.text_primary,
            "--color-text-secondary": self.text_secondary,
            "--color-text-muted": self.text_muted,
            "--color-text-inverse": self.text_inverse,
            "--color-border": self.border,
        }


@register_setting(icon="cogs")
class IntegrationSettings(BaseGenericSetting):
    """Third-party keys the frontend needs at runtime."""

    google_analytics_id = models.CharField(max_length=40, blank=True)
    google_tag_manager_id = models.CharField(max_length=40, blank=True)
    facebook_pixel_id = models.CharField(max_length=40, blank=True)
    lead_notification_email = models.EmailField(
        blank=True, help_text="Default recipient for enquiry form submissions."
    )
    sdk_base_url = models.URLField(
        blank=True, help_text="Travories SDK base URL used for SDK-sourced packages."
    )
    booking_widget_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Integrations"
