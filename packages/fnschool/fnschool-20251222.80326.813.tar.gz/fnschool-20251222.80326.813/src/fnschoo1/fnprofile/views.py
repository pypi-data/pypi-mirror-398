from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from fnschool import _, count_chinese_characters

from .forms import FnuserForm, FnuserLoginForm

# Create your views here.

LOGIN_URL = settings.LOGIN_URL


def fnprofile_new(request):
    form = None
    if request.method == "POST":
        form = FnuserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.username = form.cleaned_data["username"]
            user.save()
            login(request, user)
            return redirect("fnhome:home")
    else:
        form = FnuserForm()

    return render(request, "fnprofile/create.html", {"form": form})


def fnprofile_log_in(request):
    if request.method == "POST":
        form = FnuserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get("next") or reverse_lazy(
                    "fnhome:home"
                )
                return redirect(next_url)
    else:
        form = FnuserLoginForm()
    return render(request, "fnprofile/log_in.html", {"form": form})


def fnprofile_log_out(request):
    logout(request)
    return redirect("fnhome:home")


@login_required
def fnprofile_edit(request):
    if request.method == "POST":
        form = FnuserForm(request.POST, request.FILES, instance=request.user)
        print(request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request, _("Your information has been updated successfully!")
            )
            return redirect("fnhome:home")
    else:
        form = FnuserForm(instance=request.user)
    return render(request, "fnprofile/edit.html", {"form": form})


# The end.
