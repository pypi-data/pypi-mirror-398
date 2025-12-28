from typing import Any, Dict
from colorama import init as colorama_init, Fore, Style
import re
import importlib
from importlib.metadata import entry_points


class ModsonError(Exception):
    """
    Base exception for Modson-related errors.
    """
    pass


class CollisionError(ModsonError):
    """
    Exception raised when there is a module name collision.
    """
    pass


class ModsonRuntime:
    """
    Runtime class to handle dynamic importing of Meson modules via entry points.
    """
    group_name: str = 'modson.modules'
    """
    The entry point group name for Modson modules.
    """
    regex_pattern: re.Pattern[str] = re.compile(r'^mesonbuild\.modules\.(.+)$')
    """
    Regular expression pattern to match Meson module import names.
    """
    modules: Dict[str, str] | None = {}
    """
    Dictionary mapping module names to their import paths.
    """
    _import_module = staticmethod(importlib.import_module)
    """
    Reference to the original import_module function.
    """

    def __init__(self, group_name: str | None = None, regex_pattern: str | None = None):
        if regex_pattern is not None:
            self.regex_pattern = re.compile(regex_pattern)
        if group_name is not None:
            self.group_name = group_name

    def __del__(self):
        """
        Destructor to ensure the runtime is stopped properly.
        """
        self.stop_runtime()

    def import_module(self, name: str, package=None):
        """
        Custom import_module function to handle dynamic importing of Meson modules.
        """
        current_match = self.regex_pattern.match(name)
        if current_match:
            # if the module matches the Meson module pattern, handle it
            return self._handle_module_import(name, package, current_match)
        return self._import_module(name, package)

    def _handle_module_import(self, name: str, package: Any, current_match: re.Match[str]):
        """
        Handle the import of a Meson module based on the entry points.
        """
        # Load modules if not already loaded
        if not self.modules:
            self._load_entry_points()
        if self.modules is None:
            # This should never happen, but just in case
            # and for type checkers
            raise ModsonError("ModsonRuntime not properly initialized.")

        current_module = current_match.group(1)
        print(f"{Fore.CYAN}[modson]{Style.RESET_ALL} Importing module '{current_module}'")
        if current_module not in self.modules:
            return self._import_module(name, package)

        module_path = self.modules[current_module]
        return self._import_module(module_path, package)

    def initialized_runtime(self):
        """
        Initialize the Modson runtime by overriding importlib.import_module.
        """
        importlib.import_module = self.import_module

    def stop_runtime(self):
        """
        Stop the Modson runtime by restoring the original importlib.import_module.
        """
        importlib.import_module = self._import_module

    def _load_entry_points(self):
        """
        Load the entry points for Modson modules and populate the modules dictionary.
        """
        self.modules = {}
        eps = entry_points(group=self.group_name)
        for ep in eps:
            mod_name, mod_path = ep.name, ep.value
            if mod_name in self.modules:
                raise CollisionError(f"Module name collision: '{mod_name}' is already registered.")
            print(f"{Fore.GREEN}[modson]{Style.RESET_ALL} Loaded module '{mod_name}' from '{mod_path}'")
            self.modules[mod_name] = mod_path


def run_main():
    """
    Run the Meson main function with Modson runtime initialized.
    """
    from mesonbuild.mesonmain import main
    colorama_init(autoreset=True)
    runtime = ModsonRuntime()
    runtime.initialized_runtime()
    return main()
