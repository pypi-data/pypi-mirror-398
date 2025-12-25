from django.urls import path

from itoutils.django.nexus import views

app_name = "nexus_utils"

urlpatterns = [
    path("auto-login", views.auto_login, name="auto_login"),
]
