"""Forms for preservation.studio.

All public forms share a hidden honeypot field to keep spam out of the
admin inbox. The honeypot input is hidden via a CSS class (not an inline
style) so it survives a strict Content-Security-Policy.
"""

from django import forms

from .models import (
    ContactMessage,
    IntensiveApplication,
    SentimentalValueApplication,
    WaitlistEntry,
    WeekendInterest,
)


class HoneypotMixin(forms.Form):
    """Invisible anti-spam trap. Humans never see or fill it."""

    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "honeypot", "tabindex": "-1", "autocomplete": "off"}),
    )

    def clean_honeypot(self):
        value = self.cleaned_data.get("honeypot")
        if value:
            raise forms.ValidationError("Your submission was flagged as spam.")
        return value


class WaitlistForm(HoneypotMixin, forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"placeholder": "you@example.com", "autocomplete": "email"}
        )
    )

    class Meta:
        model = WaitlistEntry
        fields = ["email"]


class WeekendInterestForm(HoneypotMixin, forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={"autocomplete": "name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )

    class Meta:
        model = WeekendInterest
        fields = ["name", "email", "city"]


class SentimentalValueForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = SentimentalValueApplication
        fields = [
            "name",
            "email",
            "instagram",
            "object_description",
            "why_it_matters",
            "origin",
            "photo",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "instagram": forms.TextInput(
                attrs={"placeholder": "@yourhandle (optional)"}
            ),
            "object_description": forms.Textarea(attrs={"rows": 3}),
            "why_it_matters": forms.Textarea(attrs={"rows": 4}),
            "origin": forms.Textarea(attrs={"rows": 3}),
        }


class IntensiveApplicationForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = IntensiveApplication
        labels = {
            "about_yourself": "Tell me about yourself",
            "prior_experience": (
                "Do you have any prior experience in framing, mat cutting, "
                "or hands-on craft work?"
            ),
            "why_framing": "What drew you to custom framing specifically?",
            "goals": "What do you hope to do with this skill after the program?",
            "accommodations": (
                "Do you have any physical requirements or accommodations "
                "I should know about?"
            ),
            "questions": "Do you have any questions about me or the program?",
            "payment_plan_needed": "Will you need a payment plan?",
            "payment_plan_choice": "If yes, which plan?",
            "sponsored_seat_consideration": (
                "Would you like to be considered for the sponsored seat?"
            ),
            "sponsored_seat_statement": (
                "Please share briefly how the sponsored seat would support "
                "your practice and your ability to participate fully in the program."
            ),
            "attendance_commitment": (
                "Will you be able to show up to all 6 sessions consistently "
                "and make the most of this opportunity?"
            ),
            "interview_availability": "What days and times work best for a 10-minute call?",
            "interview_format": "Do you prefer video or phone?",
            "application_fee_status": "Have you submitted your $25 application fee?",
            "liability_consent": (
                "I understand the liability waiver requirement and am ready to sign."
            ),
        }
        help_texts = {
            "instagram_or_website": "Optional",
            "prior_experience": (
                "No experience is completely fine! This helps us understand "
                "where you're starting from."
            ),
            "goals": (
                "Frame your own work / charge for framing / work in a shop / "
                "personal use / other. Be as specific as possible."
            ),
            "accommodations": (
                "This does not disqualify you — it helps us plan accordingly."
            ),
            "questions": "Optional",
            "sponsored_seat_statement": "Optional",
            "attendance_commitment": "Optional",
        }
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "instagram_or_website",
            "about_yourself",
            "prior_experience",
            "why_framing",
            "goals",
            "accommodations",
            "questions",
            "payment_plan_needed",
            "payment_plan_choice",
            "sponsored_seat_consideration",
            "sponsored_seat_statement",
            "attendance_commitment",
            "interview_availability",
            "interview_format",
            "application_fee_status",
            "liability_consent",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel"}),
            "about_yourself": forms.Textarea(attrs={"rows": 4}),
            "prior_experience": forms.Textarea(attrs={"rows": 4}),
            "why_framing": forms.Textarea(attrs={"rows": 4}),
            "goals": forms.Textarea(attrs={"rows": 4}),
            "accommodations": forms.Textarea(attrs={"rows": 3}),
            "questions": forms.Textarea(attrs={"rows": 3}),
            "sponsored_seat_statement": forms.Textarea(attrs={"rows": 4}),
            "attendance_commitment": forms.Textarea(attrs={"rows": 3}),
            "interview_availability": forms.Textarea(attrs={"rows": 3}),
            "payment_plan_choice": forms.RadioSelect(),
            "interview_format": forms.RadioSelect(),
            "application_fee_status": forms.RadioSelect(),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_plan_needed") and not cleaned.get("payment_plan_choice"):
            self.add_error(
                "payment_plan_choice", "Please choose a payment plan."
            )
        if cleaned.get("sponsored_seat_consideration") and not cleaned.get(
            "sponsored_seat_statement"
        ):
            self.add_error(
                "sponsored_seat_statement",
                "Please share briefly how the sponsored seat would support your practice.",
            )
        return cleaned


class ContactForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "kind", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "kind": forms.Select(),
            "message": forms.Textarea(attrs={"rows": 5}),
        }
