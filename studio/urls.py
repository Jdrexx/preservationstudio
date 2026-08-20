from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.home, name="home"),
    path("intensive/", views.intensive, name="intensive"),
    path("intensive/apply/", views.intensive_apply, name="intensive_apply"),
    path("weekend/", views.weekend, name="weekend"),
    path("sentimental-value/", views.sentimental, name="sentimental"),
    path(
        "sentimental-value/apply/",
        views.sentimental_apply,
        name="sentimental_apply",
    ),
    path("about/", views.about, name="about"),
    path("about/faq/", views.about_faq, name="about_faq"),
    path("contact/", views.contact, name="contact"),
    path("contact/sponsor/", views.contact_sponsor, name="contact_sponsor"),
    path("thanks/<slug:kind>/", views.thanks, name="thanks"),
]
