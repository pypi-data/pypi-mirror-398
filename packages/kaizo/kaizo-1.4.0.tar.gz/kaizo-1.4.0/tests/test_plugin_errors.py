import importlib
from pathlib import Path

import pytest

from .common import create_fake_plugin

dummy_plugin_py = """
from kaizo.plugins import Plugin

class MyPlugin(Plugin):
    pass
"""

missing_config = """
plugins:
  nonexistent:
    source: MyPlugin
"""

invalid_plugin_config = """
plugins: not_a_dict
"""

missing_source_config = """
plugins:
  missing:
    args:
      z: 10
"""

invalid_plugin_module_config = """
plugins:
  invalid: 123
"""

bad_plugin_config = """
plugins:
  bad: MyPlugin
"""

wrong_plugin_config = """
plugins:
  wrong: MyPlugin
"""
wrong_plugin_py = """
class MyPlugin:
    pass
"""

using_invalid_plugin_config = """
invalid:
  module: plugin
  source: invalid
"""

plugin_not_found_config = """
plugins:
  dummy: MyPlugin
not_found:
  module: plugin
  source: not_found
"""


def test_plugin_missing_module(tmp_path: Path) -> None:
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(missing_config)

    with pytest.raises(ImportError):
        kaizo.ConfigParser(cfg_file)


def test_plugin_invalid_type(tmp_path: Path) -> None:
    kaizo = importlib.import_module("kaizo")

    cfg = tmp_path / "cfg.yml"
    cfg.write_text(invalid_plugin_config)

    with pytest.raises(TypeError):
        kaizo.ConfigParser(cfg)


def test_plugin_missing_source_key(tmp_path: Path) -> None:
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(missing_source_config)

    with pytest.raises(ValueError, match="source is required for missing plugin"):
        kaizo.ConfigParser(cfg_file)


def test_plugin_missing_source_attr(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "bad", body="")
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(bad_plugin_config)

    with pytest.raises(AttributeError):
        kaizo.ConfigParser(cfg_file)


def test_plugin_invalid_module(tmp_path: Path) -> None:
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(invalid_plugin_module_config)

    with pytest.raises(TypeError):
        kaizo.ConfigParser(cfg_file)


def test_plugin_not_subclass(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "wrong", body=wrong_plugin_py)
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(wrong_plugin_config)

    with pytest.raises(TypeError):
        kaizo.ConfigParser(cfg_file)


def test_using_invalid_plugin(tmp_path: Path) -> None:
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(using_invalid_plugin_config)

    parser = kaizo.ConfigParser(cfg_file)

    with pytest.raises(ValueError, match="plugins are not given"):
        parser.parse()


def test_plugin_not_found(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "dummy", body=dummy_plugin_py)
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(plugin_not_found_config)

    parser = kaizo.ConfigParser(cfg_file)

    with pytest.raises(ValueError, match="plugin not_found not found"):
        parser.parse()
