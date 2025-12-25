from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm
from fnschool import _

from .models import Profile


class ProfileLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("User Name"),
        widget=forms.TextInput(attrs={"placeholder": _("User Name")}),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Password")}),
    )


class ProfileForm(ModelForm):
    username = forms.CharField(
        max_length=128,
        label=_("User Name"),
        widget=forms.TextInput(attrs={"placeholder": _("User Name")}),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Password")}),
    )
    password_confirm = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={"placeholder": _("Confirm Password")}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].widget.attrs.update(
            {"class": "form-control-file"}
        )

    class Meta:
        current_year = date.today().year
        year_range = list(range(current_year - 100, current_year + 1))
        model = Profile
        fields = [
            "username",
            "phone",
            "affiliation",
            "superior_department",
            "date_of_birth",
            "gender",
            "address",
            "avatar",
            "bio",
        ]
        widgets = {
            "date_of_birth": forms.SelectDateWidget(
                years=year_range,
                attrs={"style": "width: 33.33%; display: inline-block;"},
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            raise forms.ValidationError("Passwords do not match")


# The end.
