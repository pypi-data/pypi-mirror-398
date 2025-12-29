from django.urls import include, path

urlpatterns = [
    path("cartouche/", include("cartouche.urls")),
]
