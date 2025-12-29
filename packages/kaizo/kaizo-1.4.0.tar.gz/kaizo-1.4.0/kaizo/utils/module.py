import importlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any


class ModuleLoader:
    @staticmethod
    def load_python_module(path: Path) -> ModuleType:
        if not path.is_file():
            msg = f"Local Python file not found: {path}"
            raise FileNotFoundError(msg)

        module_name = path.stem
        spec = spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            msg = f"Failed to load module from: {path}"
            raise ImportError(msg)

        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def load_object(module_path: str, object_name: str) -> Any:
        try:
            module = importlib.import_module(module_path)
            if not hasattr(module, object_name):
                msg = f"Module '{module_path}' has no attribute '{object_name}'"
                raise AttributeError(msg)
            return getattr(module, object_name)
        except ModuleNotFoundError as e:
            msg = f"Could not import module '{module_path}': {e}"
            raise ImportError(msg) from e
