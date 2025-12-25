import contextlib
import io
import logging
from unittest import mock

import pytest


@pytest.fixture
def capture_stream_handler_log(request):
    # Workaround capsys/capfd not working, see https://github.com/pytest-dev/pytest/issues/5997
    @contextlib.contextmanager
    def capture_stream_handler(logger):
        with contextlib.ExitStack() as stack:
            captured = io.StringIO()
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    stack.enter_context(mock.patch.object(handler, "stream", captured))
            yield captured

    return capture_stream_handler


@pytest.fixture
def mock_nexus_token():
    with mock.patch("itoutils.django.nexus.views.generate_token", return_value="JWT") as mocked:
        yield mocked
