from pathlib import Path

from kaizo import ConfigParser

X = 5

main_py = """
import math
def pow(x,y):
  return math.pow(x,y)
"""

simple_config = """
x: .{injected}
"""

kwargs_config = """
local: main.py
implicit:
  module: local
  source: pow
  call: true
  args:
    - .{injected}
    - 2
explicit:
  module: local
  source: pow
  call: true
  args:
    x: .{injected}
    y: 2
"""


def test_simple_injection(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(simple_config)

    parser = ConfigParser(cfg_file, kwargs={"injected": X})
    out = parser.parse()
    assert out["x"] == X


def test_kwargs_injection(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(kwargs_config)

    parser = ConfigParser(cfg_file, kwargs={"injected": X})
    out = parser.parse()
    assert out["implicit"] == X**2
    assert out["explicit"] == X**2
