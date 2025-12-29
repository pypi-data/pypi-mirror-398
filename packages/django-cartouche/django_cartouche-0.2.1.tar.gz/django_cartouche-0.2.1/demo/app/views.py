from django.shortcuts import render
from django.utils.translation import activate
from django.utils.translation import gettext as _


def index(request):
    activate("es")  # Force Spanish for demo
    context = {
        "title": _("Welcome"),
        "greeting": _("Hello, world!"),
        "description": _("This is a demo of django-cartouche."),
        "instructions": _("Blue underline = translated. Orange = untranslated. Click to edit."),
        # Untranslated strings to demonstrate the feature
        "untranslated_note": _("This string has no translation yet."),
        "untranslated_action": _("Add a translation by clicking here."),
    }
    return render(request, "app/index.html", context)
