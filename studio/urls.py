from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.home, name="home"),
    path("intensive/", views.intensive, name="intensive"),
    path("weekend/", views.weekend, name="weekend"),
    path("sentimental-value/", views.sentimental, name="sentimental"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("thanks/<slug:kind>/", views.thanks, name="thanks"),
]
