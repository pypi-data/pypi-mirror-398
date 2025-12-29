from django.shortcuts import render
from django.utils.translation import gettext as _


def index(request):
    context = {
        "title": _("Welcome"),
        "greeting": _("Hello, world!"),
        "description": _("This is a demo of django-cartouche."),
        "instructions": _("Click on any translated text to edit it inline."),
    }
    return render(request, "app/index.html", context)
