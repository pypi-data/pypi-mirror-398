import importlib

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # name = "profiles"
    name = "patches.202511012053_copy_profiles_to_fnprofile_data.profiles"

    def ready(sef):
        importlib.import_module(
            "patches.202511012053_copy_profiles_to_fnprofile_data.profiles.signals"
        )


# The end.
