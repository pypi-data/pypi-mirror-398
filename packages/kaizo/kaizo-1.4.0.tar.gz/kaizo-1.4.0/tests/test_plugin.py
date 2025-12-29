import importlib
from pathlib import Path

from .common import create_fake_plugin

X = 7
Y = 6
VAL = 2

correct_plugin_config = """
plugins:
  correct: MyPlugin
"""
correct_plugin_py = """
from kaizo import Plugin

class MyPlugin(Plugin):
    pass
"""

plugin_with_args_config = f"""
plugins:
  dummy:
    source: MyPlugin
    args:
      x: {X}
      y: {Y}
"""
plugin_with_args_py = """
from kaizo import Plugin

class MyPlugin(Plugin):
    def __init__(self, x,y):
        self.x = x
        self.y = y
"""

using_plugin_config = f"""
plugins:
  dummy: MyPlugin
fn:
  module: plugin
  source: dummy
  call: sqrt
  args:
    - {VAL}
"""
using_plugin_py = """
import math
from kaizo import Plugin

class MyPlugin(Plugin):
    def sqrt(self, num):
      return math.sqrt(num)
"""


def test_plugin_subclass(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "correct", body=correct_plugin_py)
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(correct_plugin_config)

    parser = kaizo.ConfigParser(cfg_file)
    assert parser.plugins is not None
    assert "correct" in parser.plugins


def test_plugin_with_args(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "dummy", body=plugin_with_args_py)
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(plugin_with_args_config)

    parser = kaizo.ConfigParser(cfg_file)
    obj = parser.plugins["dummy"]

    assert isinstance(obj, kaizo.utils.FnWithKwargs)

    plugin = obj()
    assert plugin.x == X
    assert plugin.y == Y


def test_using_plugin(tmp_path: Path) -> None:
    create_fake_plugin(tmp_path, "dummy", body=using_plugin_py)
    kaizo = importlib.import_module("kaizo")

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(using_plugin_config)

    parser = kaizo.ConfigParser(cfg_file)

    out = parser.parse()
    entry = out["fn"]

    assert entry == VAL**0.5
