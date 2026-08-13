"""
Custom REST endpoints that sit next to the Wagtail pages API:

    /api/v2/site/            brand, navigation, footer, theme, integrations
    /api/v2/block-registry/  block type -> React component contract
    /api/v2/videos/          video library
    /api/v2/packages/        catalog packages (list + detail by slug)
    /api/v2/destinations/    catalog destinations
    /api/v2/testimonials/    catalog testimonials
    /api/v2/leads/           POST an enquiry / newsletter signup
    /api/v2/auth/            Google sign-in and traveler onboarding
    /api/v2/page-by-path/    full page payload for a frontend route
"""

import datetime
import json
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Sum, Value, When
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Page, Site

from apps.catalog.models import Destination, Package, PackageRatingSummary, Testimonial, TravelerReview
from apps.catalog.serializers import (
    TravelerReviewWriteSerializer,
    serialize_destination,
    serialize_package,
    serialize_testimonial,
)
from apps.core.api.pagination import LumoraPagination
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

logger = logging.getLogger(__name__)


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
    queryset = Package.objects.filter(is_active=True).select_related("image", "destination", "rating_summary")
    serialize = staticmethod(serialize_package)

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "action", None) == "retrieve":
            return queryset.prefetch_related(
                "highlights",
                "itinerary__image",
                "gallery__image",
                "included_items",
                "testimonials__avatar",
            )
        return queryset

    def filter_queryset(self, queryset, request):
        params = request.query_params
        if params.get("popular") in {"1", "true", "yes"}:
            queryset = queryset.filter(is_popular=True)
        if params.get("category"):
            queryset = queryset.filter(category=params["category"])
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
    queryset = Destination.objects.all().select_related("image").prefetch_related(
        Prefetch(
            "packages",
            queryset=Package.objects.filter(is_active=True).order_by("price", "pk"),
            to_attr="starting_packages",
        )
    )
    serialize = staticmethod(serialize_destination)

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "action", None) == "retrieve":
            return queryset.prefetch_related(
                Prefetch(
                    "packages",
                    queryset=Package.objects.filter(is_active=True).select_related("image", "destination"),
                    to_attr="active_packages",
                )
            )
        return queryset

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


def _review_author_name(review):
    profile = getattr(review.user, "traveler_profile", None)
    return (profile.full_name if profile else "").strip() or review.user.email.split("@")[0]


def _serialize_traveler_review(review, request):
    return {
        "id": review.pk,
        "author_name": _review_author_name(review),
        "rating": review.rating,
        "body": review.body,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
        "is_mine": bool(request.user.is_authenticated and review.user_id == request.user.pk),
    }


def _package_rating_values(package):
    traveler = package.traveler_reviews.aggregate(total=Count("id"), total_rating=Sum("rating"))
    testimonials = package.testimonials.aggregate(total=Count("id"), total_rating=Sum("rating"))
    total = (traveler["total"] or 0) + (testimonials["total"] or 0)
    rating_sum = (traveler["total_rating"] or 0) + (testimonials["total_rating"] or 0)
    distribution = {
        rating: package.traveler_reviews.filter(rating=rating).count()
        + package.testimonials.filter(rating=rating).count()
        for rating in range(1, 6)
    }
    return {
        "total_reviews": total,
        "rating_sum": rating_sum,
        "average_rating": round(rating_sum / total, 1) if total else 0,
        "one_star": distribution[1],
        "two_star": distribution[2],
        "three_star": distribution[3],
        "four_star": distribution[4],
        "five_star": distribution[5],
    }


def _recalculate_package_rating(package):
    """Keep package cards and rating breakdowns correct after review changes."""

    values = _package_rating_values(package)
    PackageRatingSummary.objects.update_or_create(
        package=package,
        defaults=values,
    )
    package.rating = values["average_rating"]
    package.review_count = values["total_reviews"]
    package.save(update_fields=["rating", "review_count"])


class PackageReviewView(APIView):
    """Public review listing plus authenticated one-review-per-user mutations."""

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method in {"POST", "PATCH", "DELETE"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    @staticmethod
    def get_package(request):
        package_ref = str(request.query_params.get("package") or "").strip()
        if not package_ref:
            return None
        lookup = {"pk": int(package_ref)} if package_ref.isdigit() else {"slug": package_ref}
        return Package.objects.filter(is_active=True, **lookup).first()

    def get(self, request):
        package = self.get_package(request)
        if package is None:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)

        queryset = TravelerReview.objects.filter(package=package).select_related("user", "user__traveler_profile")
        if request.user.is_authenticated:
            queryset = queryset.order_by(
                Case(
                    When(user=request.user, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
                "-updated_at",
                "-id",
            )
        paginator = LumoraPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        values = _package_rating_values(package)
        return paginator.get_paginated_response(
            [_serialize_traveler_review(review, request) for review in page],
            extra={
                "summary": {
                    "total": values["total_reviews"],
                    "average": float(values["average_rating"]),
                    "distribution": {
                        "1": values["one_star"],
                        "2": values["two_star"],
                        "3": values["three_star"],
                        "4": values["four_star"],
                        "5": values["five_star"],
                    },
                }
            },
        )

    @transaction.atomic
    def post(self, request):
        package = self.get_package(request)
        if package is None:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TravelerReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = TravelerReview.objects.create(package=package, user=request.user, **serializer.validated_data)
        except IntegrityError:
            return Response({"detail": "You already have a review for this package. Update or delete it instead."}, status=status.HTTP_409_CONFLICT)
        _recalculate_package_rating(package)
        return Response({"review": _serialize_traveler_review(review, request)}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request):
        package = self.get_package(request)
        if package is None:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)
        review = TravelerReview.objects.filter(package=package, user=request.user).first()
        if review is None:
            return Response({"detail": "Your review was not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TravelerReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.rating = serializer.validated_data["rating"]
        review.body = serializer.validated_data["body"]
        review.save(update_fields=["rating", "body", "updated_at"])
        _recalculate_package_rating(package)
        return Response({"review": _serialize_traveler_review(review, request)})

    @transaction.atomic
    def delete(self, request):
        package = self.get_package(request)
        if package is None:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)
        review = TravelerReview.objects.filter(package=package, user=request.user).first()
        if review is None:
            return Response({"detail": "Your review was not found."}, status=status.HTTP_404_NOT_FOUND)
        review.delete()
        _recalculate_package_rating(package)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    permission_classes = [AllowAny]
    throttle_scope = "leads"

    KNOWN_FIELDS = {"name", "email", "phone", "message"}
    MAX_FIELDS = 60
    MAX_EXTRA_VALUE_LENGTH = 2_000

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}

        if len(payload) > self.MAX_FIELDS:
            return Response(
                {"ok": False, "errors": {"form": "Too many form fields."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consent = payload.get("consent") in {True, 1, "1", "true", "yes", "on"}
        if not consent:
            return Response(
                {"ok": False, "errors": {"consent": "Consent is required to submit this form."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        started_at = payload.get("form_started_at")
        if started_at:
            try:
                elapsed = timezone.now().timestamp() - float(started_at)
                if elapsed < 1.5:
                    return Response({"ok": True}, status=status.HTTP_201_CREATED)
            except (TypeError, ValueError):
                pass

        # Honeypot: a filled hidden field means a bot.
        if payload.get("company_website"):
            return Response({"ok": True}, status=status.HTTP_201_CREATED)

        form_key = str(payload.get("form_key") or "enquiry")[:60]
        data = {}
        excluded_fields = {
            "form_key", "company_website", "page_id", "package_id", "package_slug", "source_url", "consent", "form_started_at"
        }
        for key, value in payload.items():
            if key in excluded_fields:
                continue
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            data[str(key)[:80]] = str(value)[: self.MAX_EXTRA_VALUE_LENGTH]

        email = str(payload.get("email") or "").strip()
        name = str(payload.get("name") or payload.get("full_name") or "").strip()
        phone = str(payload.get("phone") or "").strip()
        if email:
            try:
                validate_email(email)
            except ValidationError:
                return Response(
                    {"ok": False, "errors": {"email": "Enter a valid email address."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not email and not phone:
            return Response(
                {"ok": False, "errors": {"email": "Provide an email address or a phone number."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = LeadSubmission(
            form_key=form_key,
            name=name[:200],
            email=email[:254],
            phone=phone[:40],
            message=str(payload.get("message") or "")[:10_000],
            data=data,
            source_url=str(payload.get("source_url") or "")[:200],
            consent_given=True,
            consent_at=timezone.now(),
        )
        if payload.get("page_id"):
            lead.page = Page.objects.filter(pk=payload["page_id"]).first()
        package_ref = payload.get("package_id") or payload.get("package_slug")
        if package_ref:
            package_ref = str(package_ref)
            package_query = {"pk": int(package_ref)} if package_ref.isdigit() else {"slug": package_ref}
            lead.package = Package.objects.filter(**package_query).first()
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

        try:
            send_mail(
                subject=f"[Lumora Treks] New {lead.form_key} submission",
                message=(
                    f"Name: {lead.name}\nEmail: {lead.email}\nPhone: {lead.phone}\n\n"
                    f"{lead.message}\n\nAll fields: {lead.data}"
                ),
                from_email=recipient,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Lead notification failed for submission %s", lead.pk)


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
