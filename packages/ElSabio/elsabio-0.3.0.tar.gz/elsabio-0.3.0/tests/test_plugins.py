# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Unit tests for the module plugins."""

# Standard library
from typing import Any

# Third party
import pytest

# Local
import elsabio.plugins
from elsabio.exceptions import PluginError
from elsabio.plugins import (
    TARIFF_ANALYZER_GROUP,
    get_plugin,
    get_plugin_api_version,
    resolve_plugins,
)

# ==================================================================================================
# Fixtures
# ==================================================================================================


def plugin_function() -> int:
    r"""A dummy plugin function."""

    return 1


class PluginFunctionWithAPIVersion:
    r"""A plugin function with an API version defined."""

    __plugin_api_version__ = '1.0'

    def __call__(self, **_kwargs: Any) -> int:
        return 2


@pytest.fixture
def plugin_registry_with_plugins(monkeypatch: pytest.MonkeyPatch) -> dict[tuple[str, str], object]:
    r"""A mocked plugin registry with 2 plugins for the Tariff Analyzer module."""

    mocked_plugin_registry = {
        (TARIFF_ANALYZER_GROUP, 'get_tariff_analyzer_facilites'): plugin_function,
        (TARIFF_ANALYZER_GROUP, 'get_facility_contracts'): PluginFunctionWithAPIVersion(),
    }

    monkeypatch.setattr(elsabio.plugins, 'plugin_registry', mocked_plugin_registry)

    return mocked_plugin_registry


# ==================================================================================================
# Tests
# ==================================================================================================


class TestResolveAndGetPlugins:
    r"""Tests for the function `resolve_plugins`."""

    def test_resolve_and_get_plugins(
        self, plugin_registry_with_plugins: dict[tuple[str, str], object]
    ) -> None:
        r"""Test to resolve all available plugins and retrieve them."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        resolve_plugins()

        # Verify
        # ===========================================================
        for key, value in plugin_registry_with_plugins.items():
            group, name = key
            plugin = get_plugin(group=group, name=name)

            assert plugin is value, f'Plugin ({group=}, {name=}) is incorrect!'

        # Clean up - None
        # ===========================================================

    @pytest.mark.raises
    def test_plugin_not_found(self) -> None:
        r"""Test to retrieve a plugin that does not exist."""

        # Setup
        # ===========================================================
        name = 'does_not_exist'
        error_msg_exp = (
            f'Plugin (group={TARIFF_ANALYZER_GROUP}, name={name}) not found in plugin registry!'
        )
        # Exercise
        # ===========================================================
        resolve_plugins()

        with pytest.raises(PluginError) as exc_info:
            get_plugin(group=TARIFF_ANALYZER_GROUP, name='does_not_exist')

        # Verify
        # ===========================================================
        error_msg = exc_info.value.args[0]
        print(error_msg)

        assert error_msg == error_msg_exp

        # Clean up - None
        # ===========================================================


class TestGetPluginAPIVersion:
    r"""Tests for the function `get_plugin_api_version`."""

    @pytest.mark.parametrize(
        ('plugin', 'api_version_exp'),
        [
            pytest.param(PluginFunctionWithAPIVersion, '1.0', id='api_version=1.0'),
            pytest.param(plugin_function, None, id='api_version=None'),
        ],
    )
    def test_get_plugin_api_version(self, plugin: object, api_version_exp: str | None) -> None:
        r"""Test to get the API version of a plugin."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        api_version = get_plugin_api_version(plugin=plugin)

        # Verify
        # ===========================================================
        assert api_version == api_version_exp

        # Clean up - None
        # ===========================================================
