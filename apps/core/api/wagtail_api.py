"""Wagtail API v2 router: pages, images and documents."""

from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet


class LumoraPagesAPIViewSet(PagesAPIViewSet):
    """
    Pages API with a couple of conveniences for the frontend:

    * `?slug=home` filters the listing by slug.
    * `?preview_token=…&draft=1` returns the latest draft revision, so the
      Next.js preview route can render unpublished edits.
    """

    known_query_parameters = PagesAPIViewSet.known_query_parameters.union(
        ["draft", "preview_token"]
    )

    def get_object(self):
        page = super().get_object()
        if self._draft_requested():
            latest = page.get_latest_revision_as_object()
            if latest is not None:
                return latest
        return page

    def _draft_requested(self):
        from django.conf import settings

        if self.request.GET.get("draft") not in {"1", "true", "yes"}:
            return False
        token = getattr(settings, "PREVIEW_TOKEN", "")
        return bool(token) and self.request.GET.get("preview_token") == token


api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", LumoraPagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)
