from django.db import models


class Item(models.Model):
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="children", null=True)

    class Meta:
        app_label = "testapp"
