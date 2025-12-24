import datetime
import os
import pathlib

import pytest

from apppy.env import Env


@pytest.fixture(scope="session")
def env_ci():
    ci_env: Env = Env.load(name="ci")
    yield ci_env


@pytest.fixture(scope="session")
def env_local():
    """
    Environment fixure which reads the currently configured
    local environment and makes this globally available to
    all tests.

    This may be helpful in the case where you would like to
    tweak local settings and run tests against them without
    having to push those settings into a code change.
    """
    test_env: Env = Env.load(name="local")
    yield test_env


@pytest.fixture
def env_overrides(request):
    """
    Environment fixure which allows any test
    to override the currently configured environment.
    """
    return getattr(request, "param", {})


@pytest.fixture
def env_unit(monkeypatch: pytest.MonkeyPatch, env_overrides):
    """
    Environment fixure which allows a unit test to
    use an Env instance.
    """
    monkeypatch.setenv("APP_ENV", current_test_name())
    return Env.load(name=current_test_name(), overrides=env_overrides)


def current_test_file() -> str:
    # Returns the base name (without suffix) of the test file currently being executed.
    test_path = os.environ["PYTEST_CURRENT_TEST"].split("::")[0]
    return pathlib.Path(test_path).stem


def current_test_name() -> str:
    test_name = os.environ["PYTEST_CURRENT_TEST"].split(":")[-1].split(" ")[0]
    # Test names can carry parameterize names (e.g. my_test[my_parameters])
    # brakcets are not safe for use in some circumstances so strip those out
    return test_name.replace("[", "_").replace("]", "_")


def current_test_time() -> str:
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
