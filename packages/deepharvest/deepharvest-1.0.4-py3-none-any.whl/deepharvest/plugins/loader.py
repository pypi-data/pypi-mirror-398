"""
Plugin Auto-Discovery and Loading
"""

import logging
import importlib
import pkg_resources
from typing import Dict, List, Type
from pathlib import Path
from .base import Plugin
from ..utils.errors import PluginLoadError

logger = logging.getLogger(__name__)


class PluginLoader:
    """Auto-discover and load plugins"""

    def __init__(self):
        self.plugins: Dict[str, Type[Plugin]] = {}
        self.loaded_plugins: Dict[str, Plugin] = {}

    def discover_plugins(self) -> Dict[str, Type[Plugin]]:
        """
        Discover plugins from entry points and local directory

        Returns:
            Dict mapping plugin names to plugin classes
        """
        plugins = {}

        # Load from entry points
        try:
            for entry_point in pkg_resources.iter_entry_points("deepharvest.plugins"):
                try:
                    plugin_class = entry_point.load()
                    if issubclass(plugin_class, Plugin):
                        plugins[entry_point.name] = plugin_class
                        logger.info(f"Discovered plugin: {entry_point.name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin {entry_point.name}: {e}")
        except Exception as e:
            logger.warning(f"Error loading entry points: {e}")

        # Load from local plugins directory
        plugins_dir = Path(__file__).parent
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name in ["__init__.py", "base.py", "loader.py"]:
                continue

            try:
                module_name = f"deepharvest.plugins.{plugin_file.stem}"
                module = importlib.import_module(module_name)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                        plugin_name = plugin_file.stem
                        plugins[plugin_name] = attr
                        logger.info(f"Discovered local plugin: {plugin_name}")
            except Exception as e:
                logger.warning(f"Failed to load plugin from {plugin_file}: {e}")

        self.plugins = plugins
        return plugins

    async def load_plugin(self, plugin_name: str, **kwargs) -> Plugin:
        """
        Load and initialize a plugin

        Args:
            plugin_name: Name of the plugin
            **kwargs: Arguments to pass to plugin constructor

        Returns:
            Initialized plugin instance
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]

        if plugin_name not in self.plugins:
            # Try to discover again
            self.discover_plugins()

        if plugin_name not in self.plugins:
            raise PluginLoadError(f"Plugin '{plugin_name}' not found")

        try:
            plugin_class = self.plugins[plugin_name]
            plugin_instance = plugin_class(**kwargs)
            await plugin_instance.initialize()
            self.loaded_plugins[plugin_name] = plugin_instance
            logger.info(f"Loaded plugin: {plugin_name}")
            return plugin_instance
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin '{plugin_name}': {e}")

    async def load_all(self, **kwargs) -> Dict[str, Plugin]:
        """Load all discovered plugins"""
        if not self.plugins:
            self.discover_plugins()

        loaded = {}
        for plugin_name in self.plugins:
            try:
                loaded[plugin_name] = await self.load_plugin(plugin_name, **kwargs)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")

        return loaded

    async def shutdown_all(self):
        """Shutdown all loaded plugins"""
        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_name}: {e}")

        self.loaded_plugins.clear()

    def list_plugins(self) -> List[str]:
        """List all discovered plugin names"""
        if not self.plugins:
            self.discover_plugins()
        return list(self.plugins.keys())
