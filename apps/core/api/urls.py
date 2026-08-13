from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.api import views
from apps.core.api.wagtail_api import api_router

router = DefaultRouter()
router.register("packages", views.PackageViewSet, basename="package")
router.register("destinations", views.DestinationViewSet, basename="destination")
router.register("testimonials", views.TestimonialViewSet, basename="testimonial")
router.register("videos", views.VideoViewSet, basename="video")

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    # Wagtail: /api/v2/pages/, /api/v2/images/, /api/v2/documents/
    path("", api_router.urls),
    path("site/", views.SiteSettingsView.as_view(), name="site-settings"),
    path("block-registry/", views.block_registry, name="block-registry"),
    path("leads/", views.LeadCreateView.as_view(), name="lead-create"),
    path("reviews/", views.PackageReviewView.as_view(), name="package-reviews"),
    path("page-by-path/", views.page_by_path, name="page-by-path"),
    path("", include(router.urls)),
]
