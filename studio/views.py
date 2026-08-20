"""Views for preservation.studio.

Every public page renders from the brief. Form POSTs save to the
database and redirect to a thank-you page (never render directly on
POST — avoids duplicate submissions on refresh).
"""

from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    ContactForm,
    IntensiveApplicationForm,
    SentimentalValueForm,
    WaitlistForm,
    WeekendInterestForm,
)

THANKS_MESSAGES = {
    "waitlist": (
        "You're on the list. We'll let you know when the next cohort opens."
    ),
    "weekend": (
        "Thanks — we'll reach out when a weekend intensive is coming to your city."
    ),
    "sentimental": (
        "Thank you for sharing your story! We are honored that you would like "
        "to preserve it. We will be in touch if your piece is selected."
    ),
    "intensive": (
        "Application received. You will hear back within one week with next "
        "steps. If you are shortlisted you'll receive an invitation to "
        "schedule your 10-minute interview."
    ),
    "contact": "Message received. We'll get back to you directly.",
}


def thanks(request, kind):
    message = THANKS_MESSAGES.get(kind, THANKS_MESSAGES["contact"])
    return render(request, "studio/thanks.html", {"message": message, "kind": kind})


def home(request):
    form = WaitlistForm()
    if request.method == "POST":
        form = WaitlistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="waitlist")
    return render(request, "studio/home.html", {"form": form})


def intensive(request):
    form = IntensiveApplicationForm()
    if request.method == "POST":
        form = IntensiveApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="intensive")
    return render(request, "studio/intensive.html", {"form": form})


def weekend(request):
    form = WeekendInterestForm()
    if request.method == "POST":
        form = WeekendInterestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="weekend")
    return render(request, "studio/weekend.html", {"form": form})


def sentimental(request):
    form = SentimentalValueForm()
    if request.method == "POST":
        form = SentimentalValueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="sentimental")
    return render(request, "studio/sentimental.html", {"form": form})


def about(request):
    return render(request, "studio/about.html")


def contact(request):
    form = ContactForm()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="contact")
    return render(request, "studio/contact.html", {"form": form})


def custom_404(request, exception):
    return render(request, "studio/404.html", status=404)


def custom_500(request):
    return render(request, "studio/500.html", status=500)
