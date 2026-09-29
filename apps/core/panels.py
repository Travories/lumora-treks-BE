"""Admin edit-form panels shared by the Lumora content models."""

from dataclasses import dataclass, field

from wagtail.admin.panels import Panel


@dataclass
class RelatedAction:
    label: str
    url: str
    icon: str = "edit"
    external: bool = False


@dataclass
class RelatedItem:
    """One row in a `RelatedLinksPanel`: a label, a short description, actions."""

    label: str
    description: str = ""
    actions: list[RelatedAction] = field(default_factory=list)


class RelatedLinksPanel(Panel):
    """
    Shortcuts from an edit screen to the content an editor usually needs next —
    e.g. from a package to its public page, destination and enquiries — so they
    don't have to leave the form and hunt through the sidebar.

    `get_items(instance, request)` returns a list of `RelatedItem`.
    """

    def __init__(self, get_items, **kwargs):
        super().__init__(**kwargs)
        self.get_items = get_items

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["get_items"] = self.get_items
        return kwargs

    class BoundPanel(Panel.BoundPanel):
        template_name = "core/panels/related_links_panel.html"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.items = self.panel.get_items(self.instance, self.request) or []

        def is_shown(self):
            return bool(self.items)

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["items"] = self.items
            return context
