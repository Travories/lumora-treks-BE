from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("google/", views.GoogleLoginView.as_view(), name="google"),
    path("me/", views.MeView.as_view(), name="me"),
    path("onboarding/", views.OnboardingView.as_view(), name="onboarding"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
