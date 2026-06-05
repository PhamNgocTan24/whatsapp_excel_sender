import os

from django import forms

from .models import Campaign


class CampaignCreateForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "template_name", "language_code", "excel_file", "dry_run"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. June Promo"}),
            "template_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. hello_world"}),
            "language_code": forms.TextInput(attrs={"class": "form-control"}),
            "excel_file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".xlsx"}),
            "dry_run": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "dry_run": "Dry run mode (no real messages sent)",
        }
        help_texts = {
            "excel_file": "Upload a .xlsx file. First row must be headers. Required column: phone.",
            "template_name": "Must match an approved WhatsApp template name.",
            "language_code": "Default: en_US",
        }

    def clean_excel_file(self):
        file = self.cleaned_data.get("excel_file")
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext != ".xlsx":
                raise forms.ValidationError("Only .xlsx files are accepted.")
            max_size = 10 * 1024 * 1024  # 10 MB
            if file.size > max_size:
                raise forms.ValidationError("File size must be under 10 MB.")
        return file
