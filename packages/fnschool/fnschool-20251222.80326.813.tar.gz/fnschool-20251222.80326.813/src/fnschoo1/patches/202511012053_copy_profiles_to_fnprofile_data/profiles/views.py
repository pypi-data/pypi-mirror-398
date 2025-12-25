from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from fnschool import _, count_chinese_characters

from .forms import ProfileForm, ProfileLoginForm

# Create your views here.

LOGIN_URL = settings.LOGIN_URL


def profile_new(request):
    form = None
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.username = form.cleaned_data["username"]
            user.save()
            login(request, user)
            return redirect("home")
    else:
        form = ProfileForm()

    return render(request, "profiles/create.html", {"form": form})


def profile_log_in(request):
    if request.method == "POST":
        form = ProfileLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get("next") or reverse_lazy("home")
                return redirect(next_url)
    else:
        form = ProfileLoginForm()
    return render(request, "profiles/log_in.html", {"form": form})


def profile_log_out(request):
    logout(request)
    return redirect("home")


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        print(request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request, _("Profile has been updated successfully!")
            )
            return redirect("home")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "profiles/edit.html", {"form": form})


# The end.
