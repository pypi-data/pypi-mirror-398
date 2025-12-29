import sys
from typing import Any, TypeVar, Union, Type

from kikyo.settings import Settings

T = TypeVar('T')


class Kikyo:
    def __init__(self, _settings: dict = None, **kwargs):
        self.settings = Settings(_settings)
        self.settings.merge(kwargs)
        self._components = {}
        self._init()

    def _init(self):
        self._init_plugins()

    def _init_plugins(self):
        if sys.version_info >= (3, 10):
            from importlib import metadata
        else:
            import importlib_metadata as metadata
        plugins = {
            entry_point.name: entry_point.load()
            for entry_point in metadata.entry_points(group='kikyo.plugins')
        }

        active_plugins = self.settings.getlist('active_plugins')
        if active_plugins:
            active_plugins = set(active_plugins)
            for name in list(plugins.keys()):
                if name not in active_plugins:
                    del plugins[name]

        inactive_plugins = self.settings.getlist('inactive_plugins')
        if inactive_plugins:
            inactive_plugins = set(inactive_plugins)
            for name in list(plugins.keys()):
                if name in inactive_plugins:
                    del plugins[name]

        for name, plugin in plugins.items():
            if hasattr(plugin, 'configure_kikyo'):
                plugin.configure_kikyo(self)

    def add_component(self, name: str, component: Any):
        self._components[name] = component

    def component(self, name: str = None, cls: Type[T] = None) -> Union[T, Any]:
        if name is not None:
            if name not in self._components:
                raise RuntimeError(f"No component named '{name}'")
            return self._components[name]
        candidates = []
        for v in self._components.values():
            if isinstance(v, cls):
                candidates.append(v)
        if len(candidates) == 0:
            raise RuntimeError(f"No such type component: {cls}")
        if len(candidates) > 1:
            raise RuntimeError(f"Got {len(candidates)} candidates of {cls}")
        return candidates[0]
