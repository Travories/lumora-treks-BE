"""
Custom REST endpoints that sit next to the Wagtail pages API:

    /api/v2/site/            brand, navigation, footer, theme, integrations
    /api/v2/block-registry/  block type -> React component contract
    /api/v2/videos/          video library
    /api/v2/packages/        catalog packages (list + detail by slug)
    /api/v2/destinations/    catalog destinations
    /api/v2/testimonials/    catalog testimonials
    /api/v2/leads/           POST an enquiry / newsletter signup
    /api/v2/page-by-path/    full page payload for a frontend route
"""

import datetime

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Page, Site

from apps.catalog.models import Destination, Package, Testimonial
from apps.catalog.serializers import (
    serialize_destination,
    serialize_package,
    serialize_testimonial,
)
from apps.cms.blocks import COMPONENT_MAP, SECTION_BLOCKS
from apps.core.models import Video
from apps.core.serializers import serialize_image, serialize_video
from apps.leads.models import LeadSubmission
from apps.navigation.models import (
    BrandSettings,
    FooterSettings,
    IntegrationSettings,
    NavigationSettings,
    ThemeSettings,
)


class DictModelViewSet(viewsets.ViewSet):
    """
    Read-only viewset backed by a queryset and a dict serializer function.

    DRF's ModelSerializer would duplicate the block serializers; reusing the
    same functions guarantees a package looks identical whether it arrives
    inside a page block or from this endpoint.
    """

    queryset = None
    serialize = None
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return self.queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset(), request)
        paginator = self.paginator_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        items = [self.serialize(obj) for obj in page]
        return paginator.get_paginated_response(items)

    def retrieve(self, request, slug=None):
        obj = self.get_object(slug)
        return Response(type(self).serialize(obj, detail=True))

    def get_object(self, slug):
        queryset = self.get_queryset()
        if slug.isdigit():
            return get_object_or_404(queryset, pk=int(slug))
        return get_object_or_404(queryset, slug=slug)

    def filter_queryset(self, queryset, request):
        return queryset

    @property
    def paginator_class(self):
        from apps.core.api.pagination import LumoraPagination

        return LumoraPagination


class PackageViewSet(DictModelViewSet):
    queryset = Package.objects.filter(is_active=True).select_related("image", "destination")
    serialize = staticmethod(serialize_package)

    def filter_queryset(self, queryset, request):
        params = request.query_params
        if params.get("popular") in {"1", "true", "yes"}:
            queryset = queryset.filter(is_popular=True)
        if params.get("destination"):
            queryset = queryset.filter(destination__slug=params["destination"])
        if params.get("difficulty"):
            queryset = queryset.filter(difficulty=params["difficulty"])
        if params.get("search"):
            queryset = queryset.filter(title__icontains=params["search"])
        if params.get("max_price"):
            try:
                queryset = queryset.filter(price__lte=float(params["max_price"]))
            except ValueError:
                pass
        return queryset


class DestinationViewSet(DictModelViewSet):
    queryset = Destination.objects.all().select_related("image")
    serialize = staticmethod(serialize_destination)

    def filter_queryset(self, queryset, request):
        params = request.query_params
        if params.get("featured") in {"1", "true", "yes"}:
            queryset = queryset.filter(is_featured=True)
        if params.get("region"):
            queryset = queryset.filter(region__iexact=params["region"])
        return queryset


class TestimonialViewSet(DictModelViewSet):
    queryset = Testimonial.objects.all().select_related("avatar")
    lookup_field = "pk"

    @staticmethod
    def serialize(obj, detail=False):
        return serialize_testimonial(obj)

    def get_object(self, slug):
        return get_object_or_404(self.get_queryset(), pk=slug)

    def filter_queryset(self, queryset, request):
        if request.query_params.get("featured") in {"1", "true", "yes"}:
            queryset = queryset.filter(is_featured=True)
        return queryset


class VideoViewSet(DictModelViewSet):
    queryset = Video.objects.all().select_related("poster")

    @staticmethod
    def serialize(obj, detail=False):
        return serialize_video(obj)

    def get_object(self, slug):
        return get_object_or_404(self.get_queryset(), pk=slug)


class SiteSettingsView(APIView):
    """Everything the layout needs: brand, nav, footer, theme, integrations."""

    def get(self, request):
        brand = BrandSettings.load(request_or_site=request)
        navigation = NavigationSettings.load(request_or_site=request)
        footer = FooterSettings.load(request_or_site=request)
        theme = ThemeSettings.load(request_or_site=request)
        integrations = IntegrationSettings.load(request_or_site=request)

        year = datetime.date.today().year

        return Response(
            {
                "brand": {
                    "site_name": brand.site_name,
                    "tagline": brand.tagline,
                    "logo": serialize_image(brand.logo, ["thumb", "card"]),
                    "logo_dark": serialize_image(brand.logo_dark, ["thumb", "card"]),
                    "logo_icon": brand.logo_icon,
                    "favicon": serialize_image(brand.favicon, ["thumb"]),
                    "default_meta_title": brand.default_meta_title,
                    "default_meta_description": brand.default_meta_description,
                    "default_share_image": serialize_image(brand.default_share_image, ["wide"]),
                    "contact": {
                        "email": brand.email,
                        "phone": brand.phone,
                        "whatsapp": brand.whatsapp,
                        "address": brand.address,
                        "map_embed_url": brand.map_embed_url,
                    },
                },
                "navigation": {
                    "sticky": navigation.sticky,
                    "announcement": {
                        "text": navigation.announcement_text,
                        "link": navigation.announcement_link,
                    }
                    if navigation.announcement_text
                    else None,
                    "items": navigation.items.stream_block.get_api_representation(navigation.items),
                    "cta_button": navigation.cta_button.stream_block.get_api_representation(
                        navigation.cta_button
                    ),
                },
                "footer": {
                    "description": footer.description,
                    "columns": footer.columns.stream_block.get_api_representation(footer.columns),
                    "socials": footer.socials.stream_block.get_api_representation(footer.socials),
                    "newsletter": {
                        "enabled": footer.newsletter_enabled,
                        "heading": footer.newsletter_heading,
                        "text": footer.newsletter_text,
                        "placeholder": footer.newsletter_placeholder,
                        "button_label": footer.newsletter_button_label,
                    },
                    "copyright_text": footer.copyright_text.replace("{year}", str(year)),
                    "secondary_text": footer.secondary_text,
                },
                "theme": {
                    "colors": {
                        name.lstrip("-").replace("-", "_"): value
                        for name, value in theme.css_variables.items()
                    },
                    "css_variables": theme.css_variables,
                },
                "integrations": {
                    "google_analytics_id": integrations.google_analytics_id,
                    "google_tag_manager_id": integrations.google_tag_manager_id,
                    "facebook_pixel_id": integrations.facebook_pixel_id,
                    "sdk_base_url": integrations.sdk_base_url,
                    "booking_widget_url": integrations.booking_widget_url,
                },
            }
        )


@api_view(["GET"])
def block_registry(request):
    """
    The contract between the two repos: every registered block, the React
    component that renders it, and its editable fields.
    """
    blocks_payload = []
    for name, block in SECTION_BLOCKS:
        blocks_payload.append(
            {
                "type": name,
                "component": COMPONENT_MAP[name],
                "label": block.meta.label or name,
                "group": getattr(block.meta, "group", ""),
                "fields": sorted(block.child_blocks.keys()),
            }
        )
    return Response({"count": len(blocks_payload), "blocks": blocks_payload})


class LeadCreateView(APIView):
    """POST a form submission. Used by the lead_form block and the newsletter."""

    throttle_scope = "leads"

    KNOWN_FIELDS = {"name", "email", "phone", "message"}

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}

        # Honeypot: a filled hidden field means a bot.
        if payload.get("company_website"):
            return Response({"ok": True}, status=status.HTTP_201_CREATED)

        form_key = str(payload.get("form_key") or "enquiry")[:60]
        data = {
            key: value
            for key, value in payload.items()
            if key not in {"form_key", "company_website", "page_id", "package_id", "source_url"}
        }

        email = str(payload.get("email") or "").strip()
        name = str(payload.get("name") or payload.get("full_name") or "").strip()
        if not email and not payload.get("phone"):
            return Response(
                {"ok": False, "errors": {"email": "Provide an email address or a phone number."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = LeadSubmission(
            form_key=form_key,
            name=name[:200],
            email=email[:254],
            phone=str(payload.get("phone") or "")[:40],
            message=str(payload.get("message") or ""),
            data=data,
            source_url=str(payload.get("source_url") or "")[:200],
        )
        if payload.get("page_id"):
            lead.page = Page.objects.filter(pk=payload["page_id"]).first()
        if payload.get("package_id"):
            lead.package = Package.objects.filter(pk=payload["package_id"]).first()
        lead.save()

        self._notify(request, lead)
        return Response({"ok": True, "id": lead.pk}, status=status.HTTP_201_CREATED)

    @staticmethod
    def _notify(request, lead):
        recipient = (
            IntegrationSettings.load(request_or_site=request).lead_notification_email
            or getattr(settings, "DEFAULT_FROM_EMAIL", "")
        )
        if not recipient:
            return
        from django.core.mail import send_mail

        send_mail(
            subject=f"[Lumora Treks] New {lead.form_key} submission",
            message=(
                f"Name: {lead.name}\nEmail: {lead.email}\nPhone: {lead.phone}\n\n"
                f"{lead.message}\n\nAll fields: {lead.data}"
            ),
            from_email=recipient,
            recipient_list=[recipient],
            fail_silently=True,
        )


@never_cache
def page_by_path(request):
    """
    Return a full page payload for a frontend route in one request:

        GET /api/v2/page-by-path/?path=/about

    Saves the frontend from following the redirect that Wagtail's
    `/api/v2/pages/find/` issues.
    """
    from apps.core.api.wagtail_api import LumoraPagesAPIViewSet, api_router

    path = request.GET.get("path", "/") or "/"
    site = Site.find_for_request(request)
    if site is None:
        site = Site.objects.filter(is_default_site=True).first()
    if site is None:
        return JsonResponse({"detail": "No Wagtail site is configured."}, status=404)

    components = [segment for segment in path.strip("/").split("/") if segment]
    try:
        route_result = site.root_page.localized.specific.route(request, components)
    except Http404:
        return JsonResponse({"detail": "No page found for this path."}, status=404)

    page = route_result.page
    if not page.live:
        return JsonResponse({"detail": "Page is not published."}, status=404)

    request.wagtailapi_router = api_router
    view = LumoraPagesAPIViewSet.as_view({"get": "detail_view"})
    return view(request, pk=page.pk)
