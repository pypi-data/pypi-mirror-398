from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Fnuser


@receiver(post_save, sender=User)
def create_user_fnprofile(sender, instance, created, **kwargs):
    if created:
        Fnuser.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_fnprofile(sender, instance, **kwargs):
    if hasattr(instance, "fnprofile"):
        instance.fnprofile.save()


# The end.
