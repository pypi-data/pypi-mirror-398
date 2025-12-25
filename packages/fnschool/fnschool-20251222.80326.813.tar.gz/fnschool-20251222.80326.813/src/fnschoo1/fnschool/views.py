from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render


def home_view(request):
    return redirect("fnhome:home")


# The end.
