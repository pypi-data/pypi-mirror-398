import pytest
import time_machine


@pytest.fixture(scope="session", autouse=True, name="configure_time_machine")
def configure_time_machine_fixture():
    time_machine.naive_mode = time_machine.NaiveMode.ERROR
