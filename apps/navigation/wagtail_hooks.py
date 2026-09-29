"""
"Site settings" menu: the website-wide content editors maintain (brand,
navigation, footer, theme, integrations), kept apart from Wagtail's
technical administration settings (users, sites, collections…).
"""

from wagtail import hooks
from wagtail.admin.menu import Menu, SubmenuMenuItem
from wagtail.contrib.settings.registry import SettingMenuItem

from apps.navigation.models import (
    BrandSettings,
    FooterSettings,
    IntegrationSettings,
    NavigationSettings,
    ThemeSettings,
)

SITE_SETTINGS = (
    (BrandSettings, "site"),
    (NavigationSettings, "list-ul"),
    (FooterSettings, "placeholder"),
    (ThemeSettings, "colour-palette"),
    (IntegrationSettings, "cogs"),
)

site_settings_menu = Menu(
    register_hook_name="register_site_settings_menu_item",
    construct_hook_name="construct_site_settings_menu",
)


def _site_setting_menu_item(model, icon, order):
    def build():
        return SettingMenuItem(model, icon=icon, name=model._meta.model_name, order=order)

    return build


for _order, (_model, _icon) in enumerate(SITE_SETTINGS, start=1):
    hooks.register("register_site_settings_menu_item", _site_setting_menu_item(_model, _icon, _order))


@hooks.register("register_admin_menu_item")
def register_site_settings_menu():
    return SubmenuMenuItem("Site settings", site_settings_menu, name="site-settings", icon_name="sliders", order=8000)


@hooks.register("construct_settings_menu")
def remove_site_settings_from_administration(request, menu_items):
    moved = {model for model, _icon in SITE_SETTINGS}
    menu_items[:] = [item for item in menu_items if getattr(item, "model", None) not in moved]
