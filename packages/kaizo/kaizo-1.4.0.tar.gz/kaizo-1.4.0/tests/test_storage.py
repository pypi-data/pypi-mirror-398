from pathlib import Path

from kaizo import ConfigParser

X1 = 5
X2 = 6
X3 = 7

main_py = """
def calc(x):
    return x
"""

main_config = f"""
local: main.py
x: {X1}
y:
  module: local
  source: calc
  args:
    x: {X2}
z: {X3}
x-ref: .{{x}}
y-ref: .y.{{}}
x-y-ref: .y.{{x}}
"""

implicit_config = """
local: main.py
import:
 m: main.yml
x: m.{}
y: m.y.{}
z:
  module: local
  source: calc
  args:
    - m.{}
"""

explicit_config = """
local: main.py
import:
 m: main.yml
x: m.{x}
y: m.{y}
y-x: m.y.{x}
z:
  module: local
  source: calc
  args:
    - m.{z}
"""


def test_local_ref(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(main_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["x-ref"] == X1
    assert out["y-ref"] == X2
    assert out["x-y-ref"] == X2


def test_module_implicit_ref(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    main_file = tmp_path / "main.yml"
    main_file.write_text(main_config)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(implicit_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["x"] == X1
    assert out["y"] == X2
    assert out["z"] == X3


def test_module_explicit_ref(tmp_path: Path) -> None:
    module = tmp_path / "main.py"
    module.write_text(main_py)

    main_file = tmp_path / "main.yml"
    main_file.write_text(main_config)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(explicit_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["x"] == X1
    assert out["y"] == X2
    assert out["y-x"] == X2
    assert out["z"] == X3
