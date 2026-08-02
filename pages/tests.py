from django.test import SimpleTestCase
from django.urls import resolve, reverse

from .views import HomePageView, IntroPageView


class IntroPageTest(SimpleTestCase):
    def setUp(self):
        url = reverse("pages:intro")
        self.response = self.client.get(url)

    def test_intropage_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_intropage_template(self):
        self.assertTemplateUsed(self.response, "pages/intro.html")

    def test_intropage_contains_correct_html(self):
        self.assertContains(self.response, "Your backlog, gamified")

    def test_intropage_url_resolves_intropageview(self):
        view = resolve("/")
        self.assertEqual(view.func.view_class, IntroPageView)


class HomepageTest(SimpleTestCase):
    def setUp(self):
        url = reverse("pages:home")
        self.response = self.client.get(url)

    def test_url_exists_at_correct_location(self):
        self.assertEqual(self.response.status_code, 200)

    def test_homepage_template(self):
        self.assertTemplateUsed(self.response, "pages/home.html")

    def test_homepage_contains_correct_html(self):
        self.assertContains(self.response, "Welcome")

    def test_homepage_url_resolves_homepageview(self):
        view = resolve("/home/")
        self.assertEqual(view.func.view_class, HomePageView)
