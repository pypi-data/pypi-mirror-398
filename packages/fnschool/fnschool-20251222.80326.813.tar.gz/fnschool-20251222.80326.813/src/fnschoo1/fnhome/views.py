import io
import re
from datetime import date, datetime
from decimal import (
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_UP,
    Decimal,
    getcontext,
    localcontext,
)
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.encoding import escape_uri_path
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

# Create your views here.


def home(request):
    return render(request, "fnhome/home.html")
