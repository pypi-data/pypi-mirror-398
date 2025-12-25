from django.urls import include, path

urlpatterns = [
    path("nexus/", include("itoutils.django.nexus.urls", namespace="nexus")),
]
