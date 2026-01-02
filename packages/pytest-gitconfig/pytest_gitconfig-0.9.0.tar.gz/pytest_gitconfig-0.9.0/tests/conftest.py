from __future__ import annotations

import pytest

pytest_plugins = "pytester"


@pytest.fixture(scope="session", autouse=True)
def git_env_var(sessionpatch: pytest.MonkeyPatch):
    sessionpatch.setenv("GIT_WHATEVER", "whatever")


# Just here to allow tests to verify that session-scoped defaults are not overridden
@pytest.fixture(scope="session")
def test_user_name() -> str:
    return "default user"


@pytest.fixture(scope="session")
def test_user_email() -> str:
    return "default@py.test"


@pytest.fixture(scope="session")
def test_default_branch() -> str:
    return "master"


# HACK: we add the git_env_var fixture as a dependency to ensure it is applied before
@pytest.fixture(scope="session")
def default_git_user_name(test_user_name: str, git_env_var) -> str:
    return test_user_name


@pytest.fixture(scope="session")
def default_git_user_email(test_user_email: str) -> str:
    return test_user_email


@pytest.fixture(scope="session")
def default_git_init_default_branch(test_default_branch: str) -> str:
    return test_default_branch


@pytest.fixture(scope="session")
def set_default_gitconfig(test_user_email: str) -> dict[str, str]:
    return {"some.settings": "42"}
