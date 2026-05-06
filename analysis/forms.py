# analysis/forms.py

from django import forms
from .models import YearlyRecord, MonthlyRecord


class CSVUploadForm(forms.Form):
    yearly_csv  = forms.FileField(
        required=False,
        label="Yearly deaths CSV  (yearly_deaths_by_clinic.csv)",
        widget=forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
    )
    monthly_csv = forms.FileField(
        required=False,
        label="Monthly deaths CSV  (monthly_deaths.csv)",
        widget=forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("yearly_csv") and not cleaned.get("monthly_csv"):
            raise forms.ValidationError("Upload at least one CSV file.")
        return cleaned


class YearlyRecordForm(forms.ModelForm):
    class Meta:
        model  = YearlyRecord
        fields = ["year", "births", "deaths", "clinic"]
        widgets = {
            "year":   forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "births": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "deaths": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "clinic": forms.Select(
                choices=[("clinic 1", "Clinic 1"), ("clinic 2", "Clinic 2")],
                attrs={"class": "select select-bordered w-full"},
            ),
        }


class MonthlyRecordForm(forms.ModelForm):
    class Meta:
        model  = MonthlyRecord
        fields = ["date", "births", "deaths"]
        widgets = {
            "date":   forms.DateInput(attrs={"type": "date", "class": "input input-bordered w-full"}),
            "births": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "deaths": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
        }