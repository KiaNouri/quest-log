from django.urls import path

from apps.reviews.views import ReviewDetailView, ReviewListView

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="list"),
    path("<uuid:pk>/", ReviewDetailView.as_view(), name="detail"),
]
