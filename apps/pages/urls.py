from django.urls import path

from apps.pages.views import HomePageView, IntroPageView

app_name = "pages"

urlpatterns = [
    path("home/", HomePageView.as_view(), name="home"),
    path("", IntroPageView.as_view(), name="intro"),
]
