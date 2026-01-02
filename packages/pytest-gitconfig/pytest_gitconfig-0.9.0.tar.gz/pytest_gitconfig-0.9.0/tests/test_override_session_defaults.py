from __future__ import annotations

from pytest_gitconfig import GitConfig

# Session-scoped default are already overridden by conftest.py


def test_session_fixtures_override_session_scoped_defaults(
    default_gitconfig: GitConfig,
    default_git_user_name: str,
    default_git_user_email: str,
    default_git_init_default_branch: str,
    test_user_name: str,
    test_user_email: str,
    test_default_branch: str,
):
    assert default_gitconfig.get("user.name") == test_user_name
    assert default_gitconfig.get("user.email") == test_user_email
    assert default_gitconfig.get("init.defaultBranch") == test_default_branch

    assert default_gitconfig.get("some.settings") == "42"


def test_session_fixtures_override_function_scoped_defaults(
    gitconfig: GitConfig,
    git_user_name: str,
    git_user_email: str,
    git_init_default_branch: str,
    default_git_user_name: str,
    default_git_user_email: str,
    default_git_init_default_branch: str,
    test_user_name: str,
    test_user_email: str,
    test_default_branch: str,
):
    assert gitconfig.get("user.name") == test_user_name
    assert gitconfig.get("user.email") == test_user_email
    assert gitconfig.get("init.defaultBranch") == test_default_branch
    assert gitconfig.get("some.settings") == "42"
