from __future__ import annotations

import os

import pytest

from pytest_gitconfig import GitConfig
from pytest_gitconfig.plugin import UNSET, UnsetType


@pytest.fixture
def git_user_name() -> str | UnsetType:
    return UNSET


@pytest.fixture
def git_user_email() -> str | UnsetType:
    return UNSET


@pytest.fixture
def git_init_default_branch() -> str | UnsetType:
    return UNSET


def test_gitconfig_fixture_override_defaults(
    default_gitconfig: GitConfig,
    default_git_user_name: str,
    default_git_user_email: str,
    default_git_init_default_branch: str,
):
    assert default_gitconfig.get("user.name") == default_git_user_name
    assert default_gitconfig.get("user.email") == default_git_user_email
    assert default_gitconfig.get("init.defaultBranch") == default_git_init_default_branch
    assert "GIT_WHATEVER" not in os.environ


def test_gitconfig_fixture_override(gitconfig: GitConfig):
    with pytest.raises(KeyError):
        gitconfig.get("user.name")
    with pytest.raises(KeyError):
        gitconfig.get("user.email")
    with pytest.raises(KeyError):
        gitconfig.get("init.defaultBranch")
    assert "GIT_WHATEVER" not in os.environ
