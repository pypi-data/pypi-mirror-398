import json
import logging
import uuid

import pytest
from django.core import management
from django.db import IntegrityError
from pytest_django.asserts import assertQuerySetEqual

from itoutils.django.commands import dry_runnable
from testproject.testapp.models import Item


def test_current_command_info_are_logged(capture_stream_handler_log):
    with capture_stream_handler_log(logging.getLogger()) as captured:
        management.call_command(
            "echo",
            "Hello World",
        )
    # Check that the command's info are properly logged
    log = json.loads(captured.getvalue().splitlines()[0])
    assert log["command.name"] == "testproject.testapp.management.commands.echo"
    assert uuid.UUID(log["command.run_uid"])


@pytest.mark.parametrize(
    "command,expected",
    [
        # Command with a wet_run argument
        ("testproject.testapp.management.commands.item", False),
        ("testproject.testapp.management.commands.item", True),
        # Command without a wet_run argument
        ("testproject.testapp.management.commands.echo", None),
    ],
)
@pytest.mark.django_db
def test_wet_run_info_is_logged(capture_stream_handler_log, command, expected, item):
    args = ["--wet-run"] if expected else []
    with capture_stream_handler_log(logging.getLogger()) as captured:
        management.call_command(
            # This could have been any other command inheriting from LoggedCommandMixin
            command.rsplit(".", 1)[-1],
            item.pk,
            *args,
        )
    # Check that wet run information is properly logged
    log = json.loads(captured.getvalue().splitlines()[0])
    # Check extra
    assert log["command.wet_run"] is expected
    # Check log
    if expected is False:
        assert "Command launched with wet_run=False" in captured.getvalue()
        assert "Setting transaction to be rollback as wet_run=False" in captured.getvalue()


@pytest.mark.django_db
def test_dry_runnable(item):
    assertQuerySetEqual(Item.objects.all(), [item])
    management.call_command(
        "item",
        item.pk,
        "--delete",
    )
    assertQuerySetEqual(Item.objects.all(), [item])
    management.call_command(
        "item",
        item.pk,
        "--delete",
        "--wet-run",
    )
    assertQuerySetEqual(Item.objects.all(), [])


@pytest.mark.django_db
def test_dry_runnable_check_constraints(item):
    @dry_runnable
    def command(**kwargs):
        item.parent_id = item.pk + 1
        item.save(update_fields={"parent_id"})

    with pytest.raises(
        IntegrityError,
        match='violates foreign key constraint "testapp_item_parent_id_.*_fk_testapp_item_id"',
    ):
        command(wet_run=False)
