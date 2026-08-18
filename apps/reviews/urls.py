from django.urls import path

from apps.reviews.views import ReviewListView

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="list"),
]
