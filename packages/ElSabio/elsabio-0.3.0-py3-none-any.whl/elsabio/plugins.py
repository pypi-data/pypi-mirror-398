# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functionality to manage the plugins of ElSabio."""

# Standard Library
from collections.abc import Callable
from importlib.metadata import entry_points
from typing import Any

# Local
from elsabio.exceptions import PluginError

PLUGIN_API_VERSION = '1.0'
TARIFF_ANALYZER_GROUP = 'elsabio.tariff_analyzer'
EVENT_ANALYZER_GROUP = 'elsabio.event_analyzer'
GROUPS = (TARIFF_ANALYZER_GROUP, EVENT_ANALYZER_GROUP)

type PluginFunction = Callable[..., Any]
type PluginRegistry = dict[tuple[str, str], PluginFunction]
type PluginVersion = str | tuple[str | int, ...]


plugin_registry: PluginRegistry = {}


def resolve_plugins() -> None:
    r"""Resolve available plugins and store them in the registry."""

    for group in GROUPS:
        eps = entry_points().select(group=group)
        if not eps:
            continue

        for ep in eps:
            plugin_registry[(group, ep.name)] = ep.load()


def get_plugin(group: str, name: str) -> PluginFunction:
    r"""Get a plugin from the plugin registry.

    Parameters
    ----------
    group : str
        The group the plugin belongs to.

    name : str
        The name of the plugin.

    Returns
    -------
    plugin : elsabio.plugins.PluginFunction
        The plugin function.

    Raises
    ------
    elsabio.PluginError
        If a plugin that matches `group` and `name` could not be found.
    """

    plugin = plugin_registry.get((group, name))

    if plugin is None:
        raise PluginError(f'Plugin (group={group}, name={name}) not found in plugin registry!')

    return plugin


def get_plugin_api_version(plugin: object) -> PluginVersion | None:
    r"""Get the API version of a plugin.

    The API version may be defined on the function or the module where the function is defined.

    Parameters
    ----------
    plugin : object
        The plugin for which to get the API version.

    Returns
    -------
    elsabio.plugins.PluginVersion or None
        The plugin version string or tuple. None is returned if the API version
        could not be determined for the plugin.
    """

    return getattr(
        plugin, '__plugin_api_version__', getattr(plugin.__module__, '__plugin_api_version__', None)
    )
