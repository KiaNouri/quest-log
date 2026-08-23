from django.urls import path

from apps.accounts.views import ProfileDetailView, ProfileUpdateView

app_name = "accounts"

urlpatterns = [
    path("settings/", ProfileUpdateView.as_view(), name="settings"),
    path("<str:username>/", ProfileDetailView.as_view(), name="detail"),
]
