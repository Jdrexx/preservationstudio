"""Views for preservation.studio.

Nested page structure per the launch brief:

  /                           home (waitlist form inline)
  /intensive/                 program info
  /intensive/apply/           application form
  /weekend/                   info + interest list form (inline)
  /sentimental-value/         series info
  /sentimental-value/apply/   application form
  /about/                     bio + philosophy
  /about/faq/                 FAQ
  /contact/                   email, instagram, message form
  /contact/sponsor/           sponsored seat inquiry
"""

from django.shortcuts import redirect, render

from .forms import (
    ContactForm,
    IntensiveApplicationForm,
    SentimentalValueForm,
    SponsorInquiryForm,
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
    "sponsor": (
        "Thank you for your interest in sponsoring a seat. We'll be in touch "
        "with next steps."
    ),
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
    """Parent page — program info only. The application lives at /intensive/apply/."""
    return render(request, "studio/intensive.html")


def intensive_apply(request):
    form = IntensiveApplicationForm()
    if request.method == "POST":
        form = IntensiveApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="intensive")
    return render(request, "studio/intensive_apply.html", {"form": form})


def weekend(request):
    form = WeekendInterestForm()
    if request.method == "POST":
        form = WeekendInterestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="weekend")
    return render(request, "studio/weekend.html", {"form": form})


def sentimental(request):
    """Parent page — series info only. The application lives at /sentimental-value/apply/."""
    return render(request, "studio/sentimental.html")


def sentimental_apply(request):
    form = SentimentalValueForm()
    if request.method == "POST":
        form = SentimentalValueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="sentimental")
    return render(request, "studio/sentimental_apply.html", {"form": form})


def about(request):
    """Parent page — bio + philosophy. The FAQ lives at /about/faq/."""
    return render(request, "studio/about.html")


def about_faq(request):
    return render(request, "studio/about_faq.html")


def contact(request):
    form = ContactForm()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("studio:thanks", kind="contact")
    return render(request, "studio/contact.html", {"form": form})


def contact_sponsor(request):
    """Sponsored seat inquiry — saved as a sponsorship contact message."""
    form = SponsorInquiryForm()
    if request.method == "POST":
        form = SponsorInquiryForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.kind = "sponsorship"
            message.save()
            return redirect("studio:thanks", kind="sponsor")
    return render(request, "studio/contact_sponsor.html", {"form": form})


def custom_404(request, exception):
    return render(request, "studio/404.html", status=404)


def custom_500(request):
    return render(request, "studio/500.html", status=500)
