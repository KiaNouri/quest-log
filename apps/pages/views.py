from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class IntroPageView(TemplateView):
    template_name = "pages/intro.html"
