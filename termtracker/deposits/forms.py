# deposits/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Deposit, Pension


class BootstrapFormMixin:
    """Apply Bootstrap 5 classes to all form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class DepositForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Deposit
        fields = [
            "name",
            "principal",
            "annual_rate",   # ✅ added so you can set interest
            "compounding",   # ✅ choose SIMPLE / MONTHLY / ANNUAL
            "currency",
            "start_date",
            "end_date",
            "notes",         # ✅ optional notes
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class PensionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pension
        fields = [
            "name",
            "monthly_amount",
            "tax_paid",
            "currency",
            "notes",
        ]
