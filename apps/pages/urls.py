from django.urls import path

from apps.pages.views import DashboardPageView, IntroPageView

app_name = "pages"

urlpatterns = [
    path("dashboard/", DashboardPageView.as_view(), name="dashboard"),
    path("", IntroPageView.as_view(), name="intro"),
]
