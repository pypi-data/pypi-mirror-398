from __future__ import annotations

import os
import subprocess

from pathlib import Path
from typing import Any

import pytest

from pytest_gitconfig import GitConfig

_GIT_CONFIG = ["git", "config", "--global"]


def get_config(key: str) -> str | None:
    __tracebackhide__ = True
    try:
        return subprocess.check_output([*_GIT_CONFIG, key]).strip().decode("utf-8")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return None
        raise


def set_config(key: str, value: Any):
    __tracebackhide__ = True
    subprocess.call([*_GIT_CONFIG, key, value])


def test_default_gitconfig_autouse():
    assert os.environ["GIT_CONFIG_GLOBAL"] != str(Path("~/.gitconfig"))


def test_default_gitconfig(default_gitconfig: GitConfig):
    assert default_gitconfig.path != Path("~/.gitconfig")
    assert str(default_gitconfig) == str(default_gitconfig.path)
    assert os.environ["GIT_CONFIG_GLOBAL"] == str(default_gitconfig.path)


def test_gitconfig(
    gitconfig: GitConfig,
    default_git_user_name: str,
    default_git_user_email: str,
    default_git_init_default_branch: str,
):
    assert gitconfig.path != Path("~/.gitconfig")
    assert str(gitconfig) == str(gitconfig.path)
    assert gitconfig.get("user.name") == default_git_user_name
    assert gitconfig.get("user.email") == default_git_user_email
    assert gitconfig.get("init.defaultBranch") == default_git_init_default_branch
    assert os.environ["GIT_CONFIG_GLOBAL"] == str(gitconfig.path)


def test_gitconfig_override_default_gitconfig(default_gitconfig: GitConfig, gitconfig: GitConfig):
    assert default_gitconfig.path != gitconfig.path
    assert os.environ["GIT_CONFIG_GLOBAL"] == str(gitconfig.path)


def test_gitconfig_get_existing(gitconfig: GitConfig):
    username = "John Doe"
    set_config("user.name", username)
    assert gitconfig.get("user.name") == username


@pytest.mark.parametrize("key", ("user.notfound", "not.found"), ids=("section", "option"))
def test_gitconfig_get_missing_without_fallback(gitconfig: GitConfig, key: str):
    with pytest.raises(KeyError):
        gitconfig.get(key)


@pytest.mark.parametrize("key", ("user.notfound", "not.found"), ids=("section", "option"))
def test_gitconfig_get_missing_with_fallback(gitconfig: GitConfig, key: str):
    assert gitconfig.get(key, "default") == "default"


def test_gitconfig_get_bad_key(gitconfig: GitConfig):
    with pytest.raises(ValueError):
        gitconfig.get("notdotted")


def test_gitconfig_set_dict(gitconfig: GitConfig):
    expected = "expected"
    gitconfig.set({"test.dottedDict": expected})

    assert get_config("test.dottedDict") == expected


def test_gitconfig_set_nested_dicts(gitconfig: GitConfig):
    expected = "new name"
    gitconfig.set({"test": {"nestedDicts": expected}})

    assert get_config("test.nestedDicts") == expected


def test_gitconfig_set_mixed_dict(gitconfig: GitConfig):
    expected = "expected"
    gitconfig.set({"test.dottedDict": expected, "test": {"nestedDicts": expected}})

    assert get_config("test.dottedDict") == expected
    assert get_config("test.nestedDicts") == expected


def test_gitconfig_set_key_value(gitconfig: GitConfig):
    expected = "expected"
    gitconfig.set("test.dottedDict", expected)

    assert get_config("test.dottedDict") == expected


def test_gitconfig_delete_key(gitconfig: GitConfig):
    gitconfig.delete("init.defaultBranch")

    assert get_config("init.defaultBranch") is None
    with pytest.raises(KeyError):
        gitconfig.get("init.defaultBranch")


def test_gitconfig_override_existing_value(gitconfig: GitConfig):
    expected = "new name"
    initial = get_config("user.name")
    path = str(gitconfig)
    assert initial != expected
    with gitconfig.override({"user.name": expected}) as gitcfg:
        assert get_config("user.name") == expected
        assert str(gitcfg) == path
    assert get_config("user.name") == initial


def test_gitconfig_override_new_value(gitconfig: GitConfig):
    expected = "expected"
    assert get_config("some.key") is None
    path = str(gitconfig)
    with gitconfig.override({"some.key": expected}) as gitcfg:
        assert get_config("some.key") == expected
        assert str(gitcfg) == path
    assert get_config("some.key") is None
