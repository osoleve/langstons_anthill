"""Plugin loader. Discovers and loads plugins from the plugins directory."""

import importlib
import importlib.util
from pathlib import Path
from engine.bus import bus
from engine.state import load_state

PLUGINS_DIR = Path(__file__).parent
LOADED_PLUGINS = {}


def load_plugin(plugin_path: Path):
    """Load a single plugin from a Python file."""
    if not plugin_path.suffix == '.py':
        return None
    if plugin_path.name.startswith('_'):
        return None
    if plugin_path.name == 'loader.py':
        return None

    module_name = plugin_path.stem

    try:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            print(f"[loader] ERROR: failed to create spec for {module_name}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_id = getattr(module, 'PLUGIN_ID', module_name)

        if hasattr(module, 'register'):
            state = load_state()
            module.register(bus, state)
            print(f"[loader] registered plugin: {plugin_id}")

        LOADED_PLUGINS[plugin_id] = module
        return plugin_id

    except Exception as e:
        print(f"[loader] ERROR loading plugin {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_all_plugins():
    """Load all plugins from the plugins directory."""
    loaded = []

    # Load top-level plugins
    for plugin_path in PLUGINS_DIR.glob('*.py'):
        plugin_id = load_plugin(plugin_path)
        if plugin_id:
            loaded.append(plugin_id)

    # Load card plugins
    cards_dir = PLUGINS_DIR / 'cards'
    if cards_dir.exists():
        for plugin_path in cards_dir.glob('*.py'):
            plugin_id = load_plugin(plugin_path)
            if plugin_id:
                loaded.append(plugin_id)

    return loaded


def unload_plugin(plugin_id: str):
    """Unload a plugin."""
    if plugin_id in LOADED_PLUGINS:
        module = LOADED_PLUGINS[plugin_id]
        if hasattr(module, 'unregister'):
            module.unregister(bus)
        del LOADED_PLUGINS[plugin_id]
        print(f"[loader] unloaded plugin: {plugin_id}")


def reload_plugin(plugin_id: str):
    """Reload a plugin."""
    if plugin_id in LOADED_PLUGINS:
        module = LOADED_PLUGINS[plugin_id]
        plugin_path = Path(module.__file__)
        unload_plugin(plugin_id)
        return load_plugin(plugin_path)
    return None
