import pytest


@pytest.fixture(name="item", scope="function")
def item_fixture():
    from testproject.testapp.models import Item

    item = Item()
    item.save()
    return item
