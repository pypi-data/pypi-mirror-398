from __future__ import annotations

from django.urls import path

from cartouche import views

app_name = "cartouche"

urlpatterns = [
    path("save/", views.save, name="save"),
]
