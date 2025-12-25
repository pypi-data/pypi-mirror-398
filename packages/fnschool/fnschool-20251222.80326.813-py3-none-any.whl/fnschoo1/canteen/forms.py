from datetime import date, datetime

from django import forms
from fnschool import _

from .models import Category, Consumption, Ingredient, MealType


class PurchasedIngredientsWorkBookForm(forms.Form):
    workbook_file = forms.FileField(
        label=_("Select a Spreadsheet File"),
        help_text=_("Office Open XML Spreadsheet only. (*.xlsx)"),
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            f.name
            for f in Ingredient._meta.fields
            if f.name not in ["id", "user", "updated_at", "created_at"]
        ]

        current_year = date.today().year
        year_range = list(range(current_year - 100, current_year + 1))
        widgets = {
            "storage_date": forms.SelectDateWidget(
                years=year_range,
                attrs={
                    "style": "width: 33.33%; display: inline-block;",
                },
            ),
        }


class ConsumptionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].label = ""
            self.fields[name].widget.attrs.update(
                {
                    "id": f"id_{name}_{self.instance.ingredient.id}",
                    "class": "form-control",
                }
            )
            self.fields[name].disabled = self.instance.is_disabled

    class Meta:
        model = Consumption
        fields = "__all__"
        widgets = {
            "amount_used": forms.NumberInput(
                attrs={
                    "style": "width: 95px; text-align: center; font-family: Mono;"
                }
            ),
            "date_of_using": forms.HiddenInput(),
            "ingredient": forms.HiddenInput(),
            "is_disabled": forms.HiddenInput(),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "abbreviation",
            "priority",
            "pin_to_consumptions_top",
            "is_disabled",
        ]
        widgets = {
            "priority": forms.NumberInput(
                attrs={
                    "title": _(
                        "Numbers with smaller values have higher priority."
                    ),
                },
            ),
        }


class MealTypeForm(forms.ModelForm):
    class Meta:
        model = MealType
        fields = ["name", "abbreviation", "is_disabled"]


# The end.
