import re

from django import forms

from .models import Inquiry, Service


class InquiryForm(forms.ModelForm):
    # Robots fill every field; people never see this one.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "autocomplete": "off", "tabindex": "-1"}))

    class Meta:
        model = Inquiry
        fields = ["name", "phone", "email", "region", "service", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, t=None, lang="sw", **kwargs):
        super().__init__(*args, **kwargs)
        self.t = t or {}
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        self.fields["service"].empty_label = self.t.get("form_service_any", "---")
        self.fields["service"].label_from_instance = (
            lambda s: (s.title_en or s.title_sw) if lang == "en" else s.title_sw)
        labels = {"name": "form_name", "phone": "form_phone", "email": "form_email",
                  "region": "form_region", "service": "form_service", "message": "form_message"}
        for field, key in labels.items():
            self.fields[field].label = self.t.get(key, field)
        self.fields["message"].widget.attrs["placeholder"] = self.t.get("form_message_ph", "")
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["name"].widget.attrs["autocomplete"] = "name"

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not 9 <= len(digits) <= 15:
            raise forms.ValidationError(self.t.get("form_phone_bad", "Invalid phone number."))
        return phone

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
