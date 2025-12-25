from django.contrib.auth.models import (
    AbstractBaseUser,
    AbstractUser,
    BaseUserManager,
    PermissionsMixin,
    User,
)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from fnschool import *

# Create your models here.


class Gender(models.TextChoices):
    MALE = "M", _("Male")
    FEMALE = "F", _("Female")
    UNKNOWN = "U", "--"


class Profile(AbstractUser, PermissionsMixin):
    phone = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_("Phone Number")
    )
    affiliation = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Affiliation")
    )

    superior_department = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Superior department"),
    )

    date_of_birth = models.DateField(
        blank=True, null=True, verbose_name=_("Date of Birth")
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
        verbose_name=_("Gender"),
    )

    address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Address")
    )
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True, verbose_name=_("Avatar")
    )
    bio = models.TextField(
        max_length=512, blank=True, verbose_name=_("Biography")
    )

    created_at = models.DateTimeField(
        null=True, auto_now_add=True, verbose_name=_("Time of creating")
    )

    updated_at = models.DateTimeField(
        null=True, auto_now=True, verbose_name=_("Time of updating")
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return _("{0}'s Profile").format(self.username)


# The end.
