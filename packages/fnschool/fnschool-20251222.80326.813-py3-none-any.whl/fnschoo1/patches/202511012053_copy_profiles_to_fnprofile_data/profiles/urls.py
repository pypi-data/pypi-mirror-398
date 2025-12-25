from django.contrib import admin
from django.urls import include, path

from . import views

app_name = "profiles"

urlpatterns = [
    path("detail", views.profile_edit, name="detail"),
    path("log_out", views.profile_log_out, name="log_out"),
    path("create", views.profile_new, name="create"),
    path("log_in", views.profile_log_in, name="log_in"),
    path("update", views.profile_edit, name="update"),
]
# The end.
