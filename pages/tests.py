from django.test import SimpleTestCase
from django.urls import resolve, reverse

from .views import HomePageView


class HomepageTest(SimpleTestCase):
    def setUp(self):
        url = reverse("pages:home")
        self.response = self.client.get(url)

    def test_url_exists_at_correct_location(self):
        self.assertEqual(self.response.status_code, 200)

    def test_homepage_template(self):
        self.assertTemplateUsed(self.response, "home.html")

    def test_homepage_contains_correct_html(self):
        self.assertContains(self.response, "Welcome")

    def test_homepage_url_resolves_homepageview(self):
        view = resolve("/")
        self.assertEqual(view.func.view_class, HomePageView)
