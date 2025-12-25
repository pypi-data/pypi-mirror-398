import pytest
from django.apps import apps


@pytest.mark.parametrize("app_label", ["itoutils", "testapp"])
def test_apps_are_loaded(app_label):
    assert apps.get_app_config(app_label)
