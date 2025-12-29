from pathlib import Path

from kaizo import ConfigParser

X = 2
Y = 3
RESULT = X + Y

main_py = """
def add(x, y):
    return x + y
"""

relative_config = f"""
local: main.py
run:
  module: local
  source: add
  call: true
  args:
    x: {X}
    y: {Y}
"""

absolute_config = f"""
local: {{tmp_path}}/main.py
run:
  module: local
  source: add
  call: true
  args:
    x: {X}
    y: {Y}
"""


def test_relative_local_module(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(relative_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["run"] == RESULT


def test_absolute_local_module(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(absolute_config.format(tmp_path=tmp_path))

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["run"] == RESULT
