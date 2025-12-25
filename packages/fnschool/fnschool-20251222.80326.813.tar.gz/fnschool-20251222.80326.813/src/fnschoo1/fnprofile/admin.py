from django.contrib import admin

from .models import Fnuser

# Register your models here.


@admin.register(Fnuser)
class FnuserAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "phone",
        "affiliation",
        "superior_department",
        "date_of_birth",
        "address",
    ]
    search_fields = ["user__username", "phone", "address"]
    list_filter = ["date_of_birth"]

    def user(self, obj):
        if obj:
            return obj.username
        return "No User"


# The end.
