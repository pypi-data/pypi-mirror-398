from django.contrib import admin
from django.urls import include, path

from . import views

app_name = "fnprofile"

urlpatterns = [
    path("detail", views.fnprofile_edit, name="detail"),
    path("log_out", views.fnprofile_log_out, name="log_out"),
    path("create", views.fnprofile_new, name="create"),
    path("log_in", views.fnprofile_log_in, name="log_in"),
    path("update", views.fnprofile_edit, name="update"),
]
# The end.
