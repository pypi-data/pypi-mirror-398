from django.contrib import admin
from django.urls import include, path

from . import views

app_name = "fnhome"

urlpatterns = [
    path("#", views.home, name="home"),
    path("", views.home, name="home"),
]

# The end.
