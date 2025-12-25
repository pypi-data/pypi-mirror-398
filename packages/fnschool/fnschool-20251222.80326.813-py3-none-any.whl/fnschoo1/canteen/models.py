import re
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator

# Create your models here.
from django.db import models
from django.db.models import Q
from fnschool import _

meal_type_name_0 = _("Meal type 0")
category_name_0 = _("Category Name 0")


class MealType(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meal_types",
        verbose_name=_("Ingredient meal type"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Meal type name"))
    abbreviation = models.CharField(
        null=True, blank=True, max_length=100, verbose_name=_("Abbreviation")
    )
    created_at = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True,
        verbose_name=_("Creating Date"),
    )
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now=True, verbose_name=_("Time of updating")
    )

    is_disabled = models.BooleanField(
        default=False, verbose_name=_("Is Disabled")
    )

    def __str__(self):
        return self.abbreviation or self.name


class Category(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="Categories",
        verbose_name=_("Ingredient category"),
    )
    name = models.CharField(
        max_length=100, blank=True, verbose_name=_("Category name")
    )
    abbreviation = models.CharField(
        null=True, blank=True, max_length=100, verbose_name=_("abbreviation")
    )
    created_at = models.DateTimeField(
        null=True, auto_now_add=True, verbose_name=_("Creating Date")
    )
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now=True, verbose_name=_("Time of updating")
    )

    is_disabled = models.BooleanField(
        default=False, verbose_name=_("Is Disabled")
    )
    priority = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
        ],
        verbose_name=_("Category Priority"),
    )

    pin_to_consumptions_top = models.BooleanField(
        default=False, verbose_name=_("Pin to Consumptions Top")
    )

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ingredients",
        verbose_name=_("User"),
    )
    storage_date = models.DateField(verbose_name=_("Storage Date"))

    created_at = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True,
        verbose_name=_("Time of creating"),
    )

    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now=True, verbose_name=_("Time of updating")
    )

    name = models.CharField(max_length=100, verbose_name=_("Ingredient Name"))
    meal_type = models.ForeignKey(
        MealType,
        on_delete=models.PROTECT,
        related_name="ingredients",
        verbose_name=_("Ingredient Meal Type"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="ingredients",
        verbose_name=_("Ingredient Category"),
    )
    quantity = models.IntegerField(
        validators=[
            MinValueValidator(0),
        ],
        verbose_name=_("Ingredient Quantity"),
    )
    quantity_unit_name = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Unit Name of Ingredient Quantity"),
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Ingredient Total Price"),
    )

    is_ignorable = models.BooleanField(
        default=False, verbose_name=_("Is Ingredient Ignorable")
    )
    is_disabled = models.BooleanField(
        default=False, verbose_name=_("Is Ingredient Disabled")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quantity_used = 0

    @property
    def unit_price(self):
        if self.quantity > 0:
            return self.total_price / self.quantity
        return Decimal("0.0")

    @property
    def cleaned_consumptions(self):
        consumptions = self.consumptions.all()
        return consumptions

    @property
    def consuming_quantity(self):
        consumptions = self.cleaned_consumptions
        if not consumptions:
            return 0
        quantity = sum(
            [c.amount_used for c in consumptions if not c.is_disabled]
        )
        return quantity

    def get_consuming_quantity(self, final_time):
        if self.storage_date > final_time:
            return 0
        consumptions = self.cleaned_consumptions
        if not consumptions:
            return 0
        quantity = sum(
            [
                c.amount_used
                for c in consumptions
                if not c.is_disabled and c.date_of_using <= final_time
            ]
        )
        return quantity

    def get_remaining_quantity(self, final_time):
        if self.storage_date > final_time:
            return 0
        return self.quantity - self.get_consuming_quantity(final_time)

    @property
    def remaining_quantity(self):
        consumptions = self.cleaned_consumptions
        if not consumptions:
            return self.quantity
        quantity = self.quantity - sum(
            [c.amount_used for c in consumptions if not c.is_disabled]
        )
        return quantity

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = _("Ingredient List")

    def __str__(self):
        return f"{self.name} ({self.storage_date})"


class Consumption(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="consumptions",
        verbose_name=_("Ingredient"),
    )

    date_of_using = models.DateField(verbose_name=_("Date"))
    amount_used = models.IntegerField(
        verbose_name=_("Consuming Quantity"),
        validators=[MinValueValidator(0)],
    )
    is_disabled = models.BooleanField(
        default=False, verbose_name=_("Is Disabled")
    )

    class Meta:

        verbose_name = _("Consumption Record")
        verbose_name_plural = _("Consumption Records")
        ordering = ["-date_of_using"]
        constraints = [
            models.UniqueConstraint(
                fields=["ingredient", "date_of_using"],
                name="unique_ingredient_date_of_using",
            )
        ]

    def __str__(self):
        return _("{0} of {1} was consumed on {2} .").format(
            str(self.amount_used) + self.ingredient.quantity_unit_name,
            self.ingredient.name,
            self.date_of_using,
        )


# The end.
